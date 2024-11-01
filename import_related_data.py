import pandas as pd
from models import (
	Charge,
	AuditTrouble,
	AuditIssue,
	Dispute,
	Document,
	Email,
	FillDetail,
	PoReceiver,
	Report,
	RoutingRequest1,
	RoutingRequest2
)
import os
from main import normalize_column_name, convert_to_datetime, setup_database, model_map, date_fields
from csv_scraper import downloads_dir


def get_unimported_charges(session):
	print(f"\nGetting unimported Charges...")
	charges = session.query(Charge).filter_by(pulled=True, imported=False).all()
	if len(charges) > 0:
		print(f"Found {len(charges)} unimported Charges: {charges}")
	else:
		print(f"No unimported Charges found.")
	return charges


def drop_all_related_data(session, charge, model):
	print(f"        Dropping related {model.__name__} data for Charge {charge}...")
	try:
		related_records = session.query(model).filter_by(charge_number=charge).all()
		for record in related_records:
			session.delete(record)
		session.commit()
		return True
	except Exception as e:
		session.rollback()
		print(f"        Error occurred while trying to drop related {model.__name__} data: {e}")
		return False


def store_csv_data(session, directory, charge):
	try:
		imported_dirs = []
		# use map of subdirectories to models
		for subdir, model in model_map.items():
			csv_path = os.path.join(directory, subdir, f"{subdir}_{charge}.csv")
			# skip empty directories
			if not os.path.exists(csv_path):
				print(f"\n      No CSV file found for {subdir} at {csv_path}, skipping.")
				continue

			print(f"\n      Processing files in {subdir}...")
			data_dropped = drop_all_related_data(session, charge, model)
			if not data_dropped:
				continue

			print("        Preparing file data...")
			df = pd.read_csv(csv_path)

			# normalize column names to match up with Model field names
			df.columns = [normalize_column_name(col) for col in df.columns]

			# get the date fields for the current subdir/model for processing
			datetime_fields = date_fields.get(subdir, [])

			# iterate through the rows of the combined file's data frame (each row represents a record)
			for index, row in df.iterrows():
				row_data = row.to_dict()

				# parse date values to valid Date/Datetime types using mapped date fields when necessary
				for field in datetime_fields:
					if field in row_data:
						row_data[field] = convert_to_datetime(row_data[field])

				# Clean empty or null values
				for key, value in row_data.items():
					if pd.isnull(value) or (isinstance(value, str) and value.strip() == ''):
						row_data[key] = None  # or set to some default value, like ''

				# since DB fields mimic normalized column headers we can just pass the row in using kwargs
				# this dynamically creates records of any type
				record = model(**row_data)
				record.charge_number = charge
				# add the new record to the session
				session.add(record)
			print(f"      Data processed.")

		# commit all added records to the DB
		session.commit()
		return True
	except Exception as e:
		print(f"        Error occurred while trying to store related data: {e}")
		session.rollback()
		return False


def import_related_data_process(session):
	try:
		charges_to_import = get_unimported_charges(session)

		for charge in charges_to_import:
			print(f"\nSearching for files related to Charge {charge.id}...")
			processed = store_csv_data(session, downloads_dir, charge.id)
			if processed:
				print(f"Marking Charge {charge.id} imported.")
				charge.imported = True
				session.commit()
			else:
				continue

	except Exception as e:
		print(f"Error occurred while importing related data: {e}")


if __name__ == '__main__':
	try:
		engine, session = setup_database()

		charges_to_import = get_unimported_charges(session)

		for charge in charges_to_import:
			print(f"\nSearching for files related to Charge {charge.id}...")
			processed = store_csv_data(session, downloads_dir, charge.id)
			if processed:
				print(f"Marking Charge {charge.id} imported.")
				charge.imported = True
				session.commit()
			else:
				continue

	except Exception as e:
		print(f"Error occurred while importing related data: {e}")

