import os
import re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
	Base,
	Calendar,
	Charge,
	AuditIssue,
	AuditTrouble,
	Document,
	Email,
	FillDetail,
	PoReceiver,
	Report,
	RoutingRequest1,
	RoutingRequest2,
	Dispute
)
from csv_scraper import (
	run_process,
	driver,
	timestamp
)
from datetime import datetime

# map subdirectory names to models to dynamically create instances of the correct class
model_map = {
	"charge_files": Charge,
	"Audit _ Trouble Data": AuditTrouble,
	"Audit Issue Data": AuditIssue,
	"Docs & Pics": Document,
	"Emails": Email,
	"Fill Detail": FillDetail,
	"PO Receivers": PoReceiver,
	"Reports": Report,
	"Routing Requests_11": RoutingRequest1,
	"Routing Requests_12": RoutingRequest2,
	"Disputes": Dispute
}

# map date fields to parse later
date_fields = {
	"charge_files": ["transmitted"],
	"Audit _ Trouble Data": ["entry_date"],
	"Emails": ["queued_date", "generated_date"],
	"PO Receivers": ["receive_date", "start_ship", "stop_ship"],
	"Reports": ["created"],
	"Routing Requests_11": ["hdr_routing_request_dt", "hdr_ready_for_pickup_dt", "hdr_stop_pickup_dt", "hdr_start_delivery_dt", "hdr_stop_delivery_dt", "hdr_appt_dt", "hdr_complete_ts", "hdr_update_ts", "hdr_request_granted_dt", "hdr_cms_create_ts", "hdr_cms_analysis_ts", "release_dt", "ship_start_dt", "routing_request_dt", "ship_stop_dt", "late_ship_dt", "dispatched_dt", "tendered_dt", "accepted_dt", "en_route_dt", "final_destination_dt", "cancelled_dt", "cms_update_ts", "cms_create_ts", "ready_for_pickup_dt", "start_delivery_dt", "stop_delivery_dt", "appt_dt", "request_granted_dt", "early_available_dt"],
	"Disputes": ["create_date", "resolve_date", "reversal_transmitted"]
}


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


# normalize column names in CSVs so that they match up with field names in models (field names mimic column names)
def normalize_column_name(column_name):
	# Replace any non-alphanumeric character (including spaces) with an underscore
	column_name = re.sub(r"[^a-zA-Z0-9]", "_", column_name)
	# Replace multiple consecutive underscores with a single underscore
	column_name = re.sub(r"_+", "_", column_name)
	# Convert to lowercase
	return column_name.lower().strip("_")  # Strip leading or trailing underscores if any


# convert CSV dates to valid format for fields with Date or Datetime types
def convert_to_datetime(value, date_format="%m/%d/%Y %I:%M:%S %p"):
	if pd.isnull(value) or not isinstance(value, str):
		return None
	try:
		# try converting value to Datetime (will work if value contains time)
		return datetime.strptime(value, date_format)
	except ValueError:
		try:
			# then try converting  value to Date (if value does not contain time)
			date_only_format = "%m/%d/%Y"
			return datetime.strptime(value, date_only_format)
		except ValueError:
			print(f"Failed to convert {value} to datetime")
			return None


# stores data from combined_files in database (mostly dynamic)
def store_csv_data(session, combined_dir):
	# use map of subdirectories to models
	for subdir, model in model_map.items():
		# find the combined file created on the latest scrape run (uses timestamp from scrape run)
		csv_path = os.path.join(combined_dir, subdir, f"{subdir}_combined_{timestamp}.csv")
		# skip empty directories
		if not os.path.exists(csv_path):
			print(f"No CSV file found for {subdir} at {csv_path}, skipping.")
			continue

		df = pd.read_csv(csv_path)

		# normalize column names to match up with Model field names
		df.columns = [normalize_column_name(col) for col in df.columns]
		# charge files need their charge number column renamed to id to map to Charges primary key field
		if subdir == "charge_files" and "charge_number" in df.columns:
			df.rename(columns={"charge_number": "id"}, inplace=True)

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

			if subdir == "charge_files":
				existing_charge = session.query(Charge).filter_by(id=row_data['id']).first()
				if existing_charge:
					for key, value in row_data.items():
						setattr(existing_charge, key, value)
					print(f"Updated existing charge with ID {row_data['id']}")
				else:
					record = model(**row_data)
					session.add(record)
					print(f"Added new charge with ID {row_data['id']}")
			else:
				# since DB fields mimic normalized column headers we can just pass the row in using kwargs
				# this dynamically creates records of any type
				record = model(**row_data)
				# add the new record to the session
				session.add(record)
	# commit all added records to the DB
	session.commit()


# runs entire scraping, processing, and storing process
def main():
	engine, session = setup_database()

	try:
		# run webscraper
		run_process()
		combined_dir = os.path.join(os.getcwd(), "combined_files")
		# process and store scraped CSV data in DB
		print(f"\n Importing Combined CSV Data to DB...\n")
		store_csv_data(session, combined_dir)
		print("Done.")
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		# close the driver
		driver.quit()
		# end the DB session
		session.close()


if __name__ == "__main__":
	main()
