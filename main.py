import os
import re

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Charge, AuditIssue, AuditTrouble, Document, Email, FillDetail, PoReceiver, Report, RoutingRequest1, RoutingRequest2
from csv_scraper import (
	run_process,
	driver,
	timestamp
)
from datetime import datetime


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
	"Routing Requests_12": RoutingRequest2
}

date_fields = {
	"charge_files": ["transmitted"],
	"Audit _ Trouble Data": ["entry_date"],
	"Emails": ["queued_date", "generated_date"],
	"PO Receivers": ["receive_date", "start_ship", "stop_ship"],
	"Reports": ["created"],
	"Routing Requests_11": ["hdr_routing_request_dt", "hdr_ready_for_pickup_dt", "hdr_stop_pickup_dt", "hdr_start_delivery_dt", "hdr_stop_delivery_dt", "hdr_appt_dt", "hdr_complete_ts", "hdr_update_ts", "hdr_request_granted_dt", "hdr_cms_create_ts", "hdr_cms_analysis_ts", "release_dt", "ship_start_dt", "routing_request_dt", "ship_stop_dt", "late_ship_dt", "dispatched_dt", "tendered_dt", "accepted_dt", "en_route_dt", "final_destination_dt", "cancelled_dt", "cms_update_ts", "cms_create_ts", "ready_for_pickup_dt", "start_delivery_dt", "stop_delivery_dt", "appt_dt", "request_granted_dt", "early_available_dt", ""]
}


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=True)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


def normalize_column_name(column_name):
	# Replace any non-alphanumeric character (including spaces) with an underscore
	column_name = re.sub(r"[^a-zA-Z0-9]", "_", column_name)
	# Replace multiple consecutive underscores with a single underscore
	column_name = re.sub(r"_+", "_", column_name)
	# Convert to lowercase
	return column_name.lower().strip("_")  # Strip leading or trailing underscores if any


def convert_to_datetime(value, date_format="%m/%d/%Y %I:%M:%S %p"):
	if pd.isnull(value) or not isinstance(value, str):
		return None
	try:
		return datetime.strptime(value, date_format)
	except ValueError:
		try:
			date_only_format = "%m/%d/%Y"
			return datetime.strptime(value, date_only_format)
		except ValueError:
			print(f"Failed to convert {value} to datetime")
			return None


def store_csv_data(session, combined_dir):
	for subdir, model in model_map.items():
		csv_path = os.path.join(combined_dir, subdir, f"{subdir}_combined_{timestamp}.csv")
		if not os.path.exists(csv_path):
			print(f"No CSV file found for {subdir} at {csv_path}, skipping.")
			continue

		df = pd.read_csv(csv_path)
		# normalized_df = df.rename(columns=lambda x: normalize_column_name(x))
		df.columns = [normalize_column_name(col) for col in df.columns]
		if subdir == "charge_files" and "charge_number" in df.columns:
			df.rename(columns={"charge_number": "id"}, inplace=True)

		datetime_fields = date_fields.get(subdir, [])

		for index, row in df.iterrows():
			row_data = row.to_dict()

			for field in datetime_fields:
				if field in row_data:
					print(f"DATEFIELD:  {field}")
					row_data[field] = convert_to_datetime(row_data[field])

			# Clean empty or null values
			for key, value in row_data.items():
				if pd.isnull(value) or (isinstance(value, str) and value.strip() == ''):
					row_data[key] = None  # or set to some default value, like ''

			record = model(**row_data)
			session.add(record)

	session.commit()


def main():
	engine, session = setup_database()

	try:
		run_process()
		combined_dir = os.path.join(os.getcwd(), "combined_files")
		store_csv_data(session, combined_dir)
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		driver.quit()


if __name__ == "__main__":
	main()
