from models import Calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from csv_scraper import setup_driver, login, navigate_to_charges, fill_search_criteria, export_charges_csv
from main import setup_database


# Enables past calendars to be pulled and imported. takes in Int that represent the amount of months back to enable
def enable_past_calendars(session, months_back):
	try:
		today = datetime.today()
		last_of_current_month = (today + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
		n_months_ago = today - relativedelta(months=months_back)

		print(f"\nEnabling the past {months_back} months for re-pulling...")
		# Query for Calendars that fall within the months_back threshold
		previous_calendars = session.query(Calendar).filter(
			Calendar.start_date >= n_months_ago,
			Calendar.start_date < last_of_current_month + timedelta(days=1)
		).all()

		# Mark those Calendars as 'unpulled' and 'unimported' so they can be processed by the next steps
		for c in previous_calendars:
			c.pulled = False
			c.imported = False

		session.commit()
		print(f"Enabled past {months_back} months: {previous_calendars}")
	except Exception as e:
		print(f"An error occurred trying to enable the past {months_back} months.")


# Get all Calendars marked as 'unpulled'
def get_unpulled_calendars(session):
	print(f"\nGetting unpulled months...")
	calendars = session.query(Calendar).filter_by(pulled=False).all()
	if len(calendars) > 0:
		print(f"Found {len(calendars)} unpulled months: {calendars}")
	else:
		print(f"No unpulled months found.")
	return calendars


def mark_calendar_pulled(session, month):
	try:
		month.pulled = True
		session.commit()
		print(f"Month marked as pulled: {month}")
	except Exception as e:
		print(f"An error occurred while trying to marked month as pulled: {e}")


# Function with process to get charges to be used in full_process.py. Takes in a DB session and web driver
def get_charges_process(session, driver):
	try:
		# enable Calendars
		enable_past_calendars(session, 3)

		# get all unpulled Calendars
		months_to_search = get_unpulled_calendars(session)

		# Navigate and Log in to Kohls portal
		print("\nLogging in...")
		login(driver)

		print(f"\n{len(months_to_search)} Months to search")
		for month in months_to_search:
			# Get Start and End dates from Calendar instance
			start = month.start_date.strftime('%m/%d/%Y')
			end = month.end_date.strftime('%m/%d/%Y')

			print("\nNavigating to Charges Search...")
			# Navigate to Charges search page
			navigate_to_charges(driver)

			print(f"Filling search criteria for {month.month}-{month.year}...")
			# Fill search criteria with start and end dates on Calendar instance
			fill_search_criteria(driver, start, end)

			print("Clicking Export to CSV button...")
			# Export the resulting Charges to CSV
			successful_export = export_charges_csv(driver, month)
			if successful_export:
				print("CSV saved and renamed.")
				print(f"Marking {month.month}-{month.year} as pulled...")
				# Mark the Calendar instance as pulled
				mark_calendar_pulled(session, month)
	except Exception as e:
		print(f"\nError while getting charges data: {e}")


if __name__ == '__main__':
	# Replicate process to run on its own
	try:
		# When running as a stand-alone module, need to set up its own web driver and DB session instances
		engine, session = setup_database()
		enable_past_calendars(session, 2)

		months_to_search = get_unpulled_calendars(session)

		print("\nStarting Web Driver...")
		driver = setup_driver()

		# process remains the same but passes in the dedicated session and driver
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
			mark_calendar_pulled(session, month)

			# time.sleep(4)
	except Exception as e:
		print(f"\nError while getting charges data: {e}")

