from models import Calendar, Charge
import pandas as pd
from datetime import datetime, timedelta
import os
from csv_scraper import downloads_dir
from main import setup_database, normalize_column_name, convert_to_datetime


# Get all Calendars that were pulled and need to be imported
def get_unimported_calendars(session):
	print(f"\nGetting unimported months...")
	# Query for Calendars that have been pulled and are unimported to avoid potentially marking unpulled Calendars as imported
	calendars = session.query(Calendar).filter_by(pulled=True, imported=False).all()
	if len(calendars) > 0:
		print(f"Found {len(calendars)} unimported months: {calendars}")
	else:
		print(f"No unimported months found.")
	return calendars


# Get Charges CSV file using passed in Calendar instance
def get_file_to_import(calendar):
	# directory where charge files are downloaded
	directory = os.path.join(downloads_dir, "charge_files")
	if not os.path.isdir(directory):
		print("Directory not found")
		return None

	# pattern to search for. Charge files are renamed to contain the Calendar ID of the Calendar used to obtain them
	search_pattern = f"Charges_{calendar.id}_"
	for filename in os.listdir(directory):
		if filename.startswith(search_pattern) and filename.endswith('.csv'):
			print(f"Found file for {calendar.month}-{calendar.year}: {filename}")
			# If a file exists with the search pattern, return the file path
			return os.path.join(directory, filename)
	print(f"No file found for {calendar.month}-{calendar.year}")
	return None


# Process and import Charge CSV data into DB.
# params:
# Calendar instance to relate Charge to
# File to process
# Days back from current date to automatically update existing Charge with CSV data (based off 'transmitted' column)
def process_file_data(session, calendar, file, days):
	try:
		# Create data frame from CSV file
		df = pd.read_csv(file)
		# Normalize the CSVs column names to match up with the DB/Model's column names
		df.columns = [normalize_column_name(column) for column in df.columns]

		# Calculate the date n days back from current date
		days_threshold = datetime.now() - timedelta(days=days)

		# Each row represents a Charge instance
		for _, row in df.iterrows():
			row_data = row.to_dict()  # Convert the row to a dictionary to capture all columns
			row_data['id'] = row_data.pop('charge_number')  # Map charge_number to id
			row_data['calendar_id'] = calendar.id  # Assign calendar_id
			row_data['transmitted'] = convert_to_datetime(row_data['transmitted'])  # handle date type

			# Handle empty values
			for key, value in row_data.items():
				if pd.isnull(value) or (isinstance(value, str) and value.strip() == ''):
					# Convert the empty value to None to ensure compliance with python null type
					row_data[key] = None

			# Check if Charge already exists in the database
			existing_charge = session.query(Charge).filter_by(id=row_data['id']).first()
			# Grab the current row's transmitted date
			row_transmitted_date = row_data.get('transmitted')
			# Flag to track if any value in this row has changed compared to the DB (when Charge already exists within DB)
			data_changed = False

			if existing_charge:
				# Determine if any data in the row has changed
				data_changed = any(
					getattr(existing_charge, column) != row_data[column]
					for column in row_data if column in existing_charge.__dict__
				)

				# If the transmitted date is within the day threshold, we are going to replace the existing Charge instance
				if row_transmitted_date and row_transmitted_date >= days_threshold:
					print(f"Updating Charge {existing_charge.id} - Reason: transmitted in past {days} days...")
					session.delete(existing_charge)
					# Create new Charge instance with dictionary containing processed row data
					new_charge = Charge(**row_data)
					# manually update the new Charge as unpulled and unimported to ensure it gets reprocessed in later steps
					new_charge.pulled = False
					new_charge.imported = False
					# Add the new (updated) Charge
					session.add(new_charge)
				# If any data has changed, we are going to replace the existing Charge instance
				elif data_changed:
					print(f"Updating Charge {existing_charge.id} - Reason: data changed...")
					session.delete(existing_charge)
					# Create new Charge instance with dictionary containing processed row data
					new_charge = Charge(**row_data)
					# manually update the new Charge as unpulled and unimported to ensure it gets reprocessed in later steps
					new_charge.pulled = False
					new_charge.imported = False
					# Add the new (updated) Charge
					session.add(new_charge)
			else:
				print(f"Adding new Charge {row_data['id']}...")
				# If the Charge does not already exist in the DB, then just create a new one with the row_data dictionary
				new_charge = Charge(**row_data)
				new_charge.pulled = False
				new_charge.imported = False
				session.add(new_charge)  # Add new charge to the session

		# Commit all changes to the DB
		session.commit()
		print(f"File Processed.")
		# Return True since process was successful
		return True
	except Exception as e:
		print(f"Error occurred while processing file: {e}")
		# Return False since process was unsuccessful
		return False


# Function with process to import Charges to be used in full_process.py. Takes in a DB session
def import_charges_process(session):
	try:
		# Get unimported Calendars
		months = get_unimported_calendars(session)
		for month in months:
			print(f"\nFinding file for {month.month}-{month.year}...")
			# Find Charges CSV that was pulled using this Calendar instance
			charge_file = get_file_to_import(month)
			if charge_file:
				print(f"Processing file data...")
				# Process the Charge CSVs data and  import to DB. (returns True if processing is successful)
				processed = process_file_data(session, month, charge_file, 45)
				if processed:
					print(f"Marking {month.month}-{month.year} Imported.")
					# Only mark the Calendar imported if the importing process completes successfully
					month.imported = True
					session.commit()
				else:
					# If importing process is unsuccessful, continue without marking the Calendar as imported
					continue
			else:
				continue

	except Exception as e:
		print(f"\nError while importing Charges: {e}")


if __name__ == '__main__':
	# Replicate process to run on its own
	try:
		# When running as a stand-alone module, need to set up its DB session instance
		engine, session = setup_database()

		# process remains the same but passes in the dedicated session
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
