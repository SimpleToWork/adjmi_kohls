import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Charge, AuditIssue, AuditTrouble, Document, Email, FillDetail, PoReceiver, Report, RoutingRequest1, RoutingRequest2
from csv_scraper import (
	# setup_driver,
	# login,
	# navigate_to_charges,
	# fill_search_criteria,
	# export_charges_csv,
	# wait_for_file,
	# extract_charges_from_csv,
	# scrape_charge_data,
	# export_related_csvs,
	# combine_csvs
	run_process,
	driver
)
from datetime import datetime


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=True)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


def main():
	engine, session = setup_database()

	try:
		run_process()
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		driver.quit()


if __name__ == "__main__":
	main()
