import time

from csv_scraper import scrape_charge_data, setup_driver, login
from models import Charge
from main import setup_database


def get_unpulled_charges(session):
	print("\nGetting unpulled Charges...")
	charges = session.query(Charge).filter_by(pulled=False).all()
	if len(charges) > 0:
		print(f"Found {len(charges)} unpulled Charges: {charges}")
	else:
		print("No unpulled Charges found.")

	return charges


def get_related_data_process(session, driver):
	try:
		charges = get_unpulled_charges(session)

		print(f"\n{len(charges)} Charges to Scrape")
		for index, charge in enumerate(charges):
			print(f"\n[{index+1}/{len(charges)}] Scraping data for Charge {charge.id}...")
			scrape_charge_data(driver, charge.id)

			print(f"Data scraped, marking Charge {charge.id} pulled...")
			charge.pulled = True
			session.commit()
			print(f"Done: {charge}")
	except Exception as e:
		print(f"\nError occurred while getting related data: {e}")


if __name__ == '__main__':
	try:
		engine, session = setup_database()

		charges = get_unpulled_charges(session)

		print("\nStarting web driver...")
		driver = setup_driver()

		print("\nLogging in...")
		login(driver)

		print(f"\n{len(charges)} Charges to Scrape")
		for index, charge in enumerate(charges):
			print(f"\n[{index+1}/{len(charges)}] Scraping data for Charge {charge.id}...")
			scrape_charge_data(driver, charge.id)
			print(f"Data scraped, marking Charge {charge.id} pulled...")
			charge.pulled = True
			session.commit()
			print(f"Done: {charge}")
	except Exception as e:
		print(f"\nError occurred while getting related data: {e}")

