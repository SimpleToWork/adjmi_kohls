from models import Base, Calendar, Charge
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from csv_scraper import downloads_dir
from main import setup_database, normalize_column_name, convert_to_datetime


def get_unimported_calendars(session):
	print(f"\nGetting unimported months...")
	calendars = session.query(Calendar).filter_by(pulled=True, imported=False).all()
	if len(calendars) > 0:
		print(f"Found {len(calendars)} unimported months: {calendars}")
	else:
		print(f"No unimported months found.")
	return calendars


def get_file_to_import(calendar):
	directory = os.path.join(downloads_dir, "charge_files")
	if not os.path.isdir(directory):
		print("Directory not found")
		return None

	search_pattern = f"Charges_{calendar.id}_"
	for filename in os.listdir(directory):
		if filename.startswith(search_pattern) and filename.endswith('.csv'):
			print(f"Found file for {calendar.month}-{calendar.year}: {filename}")
			return os.path.join(directory, filename)
	print(f"No file found for {calendar.month}-{calendar.year}")
	return None


def process_file_data(session, calendar, file, days):
	try:
		df = pd.read_csv(file)
		df.columns = [normalize_column_name(column) for column in df.columns]

		days_threshold = datetime.now() - timedelta(days=days)

		for _, row in df.iterrows():
			row_data = row.to_dict()  # Convert the row to a dictionary to capture all columns
			row_data['id'] = row_data.pop('charge_number')  # Map charge_number to id
			row_data['calendar_id'] = calendar.id  # Assign calendar_id
			row_data['transmitted'] = convert_to_datetime(row_data['transmitted'])  # handle date type

			for key, value in row_data.items():
				if pd.isnull(value) or (isinstance(value, str) and value.strip() == ''):
					row_data[key] = None  # or set to some default value, like ''

			# Check if an existing charge exists in the database
			existing_charge = session.query(Charge).filter_by(id=row_data['id']).first()
			row_transmitted_date = row_data.get('transmitted')
			data_changed = False

			if existing_charge:
				# Determine if any data in the row has changed
				data_changed = any(
					getattr(existing_charge, column) != row_data[column]
					for column in row_data if column in existing_charge.__dict__
				)

				if row_transmitted_date and row_transmitted_date >= days_threshold:
					print(f"Updating Charge {existing_charge.id} - Reason: transmitted in past {days} days...")
					session.delete(existing_charge)
					new_charge = Charge(**row_data)
					new_charge.pulled = False
					new_charge.imported = False
					session.add(new_charge)
				elif data_changed:
					print(f"Updating Charge {existing_charge.id} - Reason: data changed...")
					session.delete(existing_charge)
					new_charge = Charge(**row_data)
					new_charge.pulled = False
					new_charge.imported = False
					session.add(new_charge)
			else:
				print(f"Adding new Charge {row_data['id']}...")
				new_charge = Charge(**row_data)
				new_charge.pulled = False
				new_charge.imported = False
				session.add(new_charge)  # Add new charge to the session

		session.commit()
		print(f"File Processed.")
		return True
	except Exception as e:
		print(f"Error occurred while processing file: {e}")
		return False


def import_charges_process(session):
	try:
		months = get_unimported_calendars(session)
		for month in months:
			print(f"\nFinding file for {month.month}-{month.year}...")
			charge_file = get_file_to_import(month)
			if charge_file:
				print(f"Processing file data...")
				processed = process_file_data(session, month, charge_file, 45)
				if processed:
					print(f"Marking {month.month}-{month.year} Imported.")
					month.imported = True
					session.commit()
				else:
					continue
			else:
				continue

	except Exception as e:
		print(f"\nError while importing Charges: {e}")


if __name__ == '__main__':
	try:
		engine, session = setup_database()

		months = get_unimported_calendars(session)
		for month in months:
			print(f"\nFinding file for {month.month}-{month.year}...")
			charge_file = get_file_to_import(month)
			if charge_file:
				print(f"Processing file data...")
				processed = process_file_data(session, month, charge_file, 45)
				if processed:
					print(f"Marking {month.month}-{month.year} Imported.")
					month.imported = True
					session.commit()
				else:
					continue
			else:
				continue

	except Exception as e:
		print(f"\nError while importing Charges: {e}")
