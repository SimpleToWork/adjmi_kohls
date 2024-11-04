import pandas as pd
from models import (
	Charge
)
import os
from main import normalize_column_name, convert_to_datetime, setup_database, model_map, date_fields
from csv_scraper import downloads_dir


# Get all Charges that were pulled and need to be imported
def get_unimported_charges(session):
	print(f"\nGetting unimported Charges...")
	# Query for Charges that have been pulled and are unimported to avoid potentially marking unpulled Charges as imported
	charges = session.query(Charge).filter_by(pulled=True, imported=False).all()
	if len(charges) > 0:
		print(f"Found {len(charges)} unimported Charges: {charges}")
	else:
		print(f"No unimported Charges found.")
	return charges


# Drop all data related to a Charge in a specified table
def drop_all_related_data(session, charge, model):
	print(f"        Dropping related {model.__name__} data for Charge {charge}...")
	try:
		# Find instances within passed in table related to passed in Charge
		related_records = session.query(model).filter_by(charge_number=charge).all()
		for record in related_records:
			# Delete each instance
			session.delete(record)
		# Commit all changes to the DB
		session.commit()
		# Return True if successful
		return True
	except Exception as e:
		# If there's an error, roll back the changes
		session.rollback()
		print(f"        Error occurred while trying to drop related {model.__name__} data: {e}")
		# Return False since it was unsuccessful
		return False


# Find, process, and store file data related to Charge
def store_csv_data(session, directory, charge):
	try:
		# Use dictionary that maps subdirectories to the appropriate models to search for and store data
		for subdir, model in model_map.items():
			# Search for a file in subdirectory containing the Charge's ID
			csv_path = os.path.join(directory, subdir, f"{subdir}_{charge}.csv")
			# If such file does not exist, continue to the next subdirectory
			if not os.path.exists(csv_path):
				print(f"\n      No CSV file found for {subdir} at {csv_path}, skipping.")
				continue

			print(f"\n      Processing files in {subdir}...")
			# If there is a file match in the current subdirectory, drop all related data in the table associated with this subdirectory
			# This is to replace/update the related data with the latest pulled data in the current file
			# Returns True if the process was successful
			data_dropped = drop_all_related_data(session, charge, model)
			# If the data was not dropped successfully, continue to the next subdirectory
			if not data_dropped:
				continue

			print("        Preparing file data...")
			# Create data frame from CSV
			df = pd.read_csv(csv_path)

			# normalize column names to match up with DB/Model field names
			df.columns = [normalize_column_name(col) for col in df.columns]

			# get the date fields for the current subdir/model for processing using dictionary that maps subdirectories to date fields
			datetime_fields = date_fields.get(subdir, [])

			# iterate through the rows of the combined file's data frame (each row represents a record)
			for index, row in df.iterrows():
				# Convert row to dictionary
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
				# Manually update the instance with the passed in Charge ID to relate it to the Charge
				record.charge_number = charge
				# add the new record to the session
				session.add(record)
			print(f"      Data processed.")

		# commit all added records to the DB
		session.commit()
		# Return True if process was successful
		return True
	except Exception as e:
		print(f"        Error occurred while trying to store related data: {e}")
		# If an error occurs, roll back the changes and return False
		session.rollback()
		return False


# Function with process to import related data to be used in full_process.py. Takes in a DB session
def import_related_data_process(session):
	try:
		# Get unimported Charges
		charges_to_import = get_unimported_charges(session)

		for charge in charges_to_import:
			print(f"\nSearching for files related to Charge {charge.id}...")
			# Search through subdirectories for CSV files containing the Charge's ID and process/import them to the DB (returns True if successful)
			processed = store_csv_data(session, downloads_dir, charge.id)
			if processed:
				print(f"Marking Charge {charge.id} imported.")
				# Only mark charges as imported if the import process was successful
				charge.imported = True
				session.commit()
			else:
				# If the import process was unsuccessful, continue to the next Charge without marking it imported
				continue

	except Exception as e:
		print(f"Error occurred while importing related data: {e}")


if __name__ == '__main__':
	# Replicate process to run on its own
	try:
		# When running as a stand-alone module, need to set up its DB session instance
		engine, session = setup_database()

		# process remains the same but passes in the dedicated session
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

