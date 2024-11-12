import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)


import re
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from data_import.models import (
	Base,
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
from datetime import datetime

# map subdirectory names to models to dynamically create instances of the correct class
model_map = {
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
	"Audit _ Trouble Data": ["entry_date"],
	"Emails": ["queued_date", "generated_date"],
	"PO Receivers": ["receive_date", "start_ship", "stop_ship"],
	"Reports": ["created"],
	"Routing Requests_11": ["hdr_routing_request_dt", "hdr_ready_for_pickup_dt", "hdr_stop_pickup_dt", "hdr_start_delivery_dt", "hdr_stop_delivery_dt", "hdr_appt_dt", "hdr_complete_ts", "hdr_update_ts", "hdr_request_granted_dt", "hdr_cms_create_ts", "hdr_cms_analysis_ts", "release_dt", "ship_start_dt", "routing_request_dt", "ship_stop_dt", "late_ship_dt", "dispatched_dt", "tendered_dt", "accepted_dt", "en_route_dt", "final_destination_dt", "cancelled_dt", "cms_update_ts", "cms_create_ts", "ready_for_pickup_dt", "start_delivery_dt", "stop_delivery_dt", "appt_dt", "request_granted_dt", "early_available_dt"],
	"Disputes": ["create_date", "resolve_date", "reversal_transmitted"]
}


def setup_database():
	# Initial connection string without specifying a database
	connection_string_base = "mysql+mysqlconnector://root:Simple123@localhost"
	engine_base = create_engine(connection_string_base, echo=False)
	with engine_base.connect() as connection:
		# Check if the database exists
		db_exists = connection.execute(text("SHOW DATABASES LIKE 'adjmi_kohls'")).fetchone()
		# Create the database if it doesn't exist
		if not db_exists:
			connection.execute(text("CREATE DATABASE adjmi_kohls"))

	# Now connect specifically to the adjmi_kohls database
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)  # This creates tables if they don't exist
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

