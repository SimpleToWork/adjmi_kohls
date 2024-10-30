from models import (
	Base,
	Calendar,
	Charge
)
import pandas as pd
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from csv_scraper import setup_driver, login, navigate_to_charges, fill_search_criteria, export_charges_csv


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session

engine, session = setup_database()


def enable_past_calendars(months_back):
	try:
		today = datetime.today()
		last_of_current_month = (today + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
		n_months_ago = today - relativedelta(months=months_back)

		print(f"\nEnabling the past {months_back} months for re-pulling...")
		previous_calendars = session.query(Calendar).filter(
			Calendar.start_date >= n_months_ago,
			Calendar.start_date < last_of_current_month + timedelta(days=1)
		).all()

		for c in previous_calendars:
			c.pulled = False

		session.commit()
		print(f"Enabled past {months_back} months: {previous_calendars}")
	except Exception as e:
		print(f"An error occurred trying to enable the past {months_back} months.")


def get_unpulled_calendars():
	print(f"\nGetting unpulled months...")
	calendars = session.query(Calendar).filter_by(pulled=False).all()
	if len(calendars) > 0:
		print(f"Found {len(calendars)} unpulled months: {calendars}")
	else:
		print(f"No unpulled months found.")
	return calendars


def mark_calendar_pulled(month):
	try:
		month.pulled = True
		session.commit()
		print(f"Month marked as pulled: {month}")
	except Exception as e:
		print(f"An error occurred while trying to marked month as pulled: {e}")


if __name__ == '__main__':
	try:
		enable_past_calendars(3)

		months_to_search = get_unpulled_calendars()

		print("\nStarting Web Driver...")
		driver = setup_driver()

		print("\nLogging in...")
		login(driver)

		print(f"\n{len(months_to_search)} Months to search")
		for month in months_to_search:
			start = month.start_date.strftime('%m/%d/%Y')
			end = month.end_date.strftime('%m/%d/%Y')
			print("\nNavigating to Charges Search...")
			navigate_to_charges(driver)
			print(f"Filling search criteria for {month.month}-{month.year}...")
			fill_search_criteria(driver, start, end)
			print("Clicking Export to CSV button...")
			export_charges_csv(driver, month)
			print("CSV saved and renamed.")
			print(f"Marking {month.month}-{month.year} as pulled...")
			mark_calendar_pulled(month)

			time.sleep(4)
	except Exception as e:
		print(f"\nError while getting charges data: {e}")

