from csv_scraper import scrape_charge_data, setup_driver, login
from models import Charge
from main import setup_database


# Get all Charges marked as 'unpulled'
def get_unpulled_charges(session):
	print("\nGetting unpulled Charges...")
	charges = session.query(Charge).filter_by(pulled=False).all()
	if len(charges) > 0:
		print(f"Found {len(charges)} unpulled Charges: {charges}")
	else:
		print("No unpulled Charges found.")

	return charges


# # Function with process to get related data to be used in full_process.py. Takes in a DB session and a web driver
def get_related_data_process(session, driver):
	try:
		# Get all unpulled Charges
		charges = get_unpulled_charges(session)

		print(f"\n{len(charges)} Charges to Scrape")
		for index, charge in enumerate(charges):
			print(f"\n[{index+1}/{len(charges)}] Scraping data for Charge {charge.id}...")
			# Navigate to and scrape all data related to Charge instance. Returns True if scrape process successfully finishes tab process
			successful_pull = scrape_charge_data(driver, charge.id)
			if successful_pull:
				print(f"Data scraped, marking Charge {charge.id} pulled...")
				# Only mark the Charge as pulled if the scraping process was successful
				charge.pulled = True
				session.commit()
				print(f"Done: {charge}")
			else:
				# Do not mark the Charge as pulled if the scraping process was not completed
				print(f"Data incomplete, Charge {charge.id} not marked as pulled.")
	except Exception as e:
		print(f"\nError occurred while getting related data: {e}")


if __name__ == '__main__':
	# Replicate process to run on its own
	try:
		# When running as a stand-alone module, need to set up its own web driver and DB session instances
		engine, session = setup_database()

		charges = get_unpulled_charges(session)

		print("\nStarting web driver...")
		driver = setup_driver()

		# process remains the same but passes in the dedicated session and driver
		print("\nLogging in...")
		login(driver)

		print(f"\n{len(charges)} Charges to Scrape")
		for index, charge in enumerate(charges):
			print(f"\n[{index+1}/{len(charges)}] Scraping data for Charge {charge.id}...")
			successful_pull = scrape_charge_data(driver, charge.id)
			if successful_pull:
				print(f"Data scraped, marking Charge {charge.id} pulled...")
				charge.pulled = True
				session.commit()
				print(f"Done: {charge}")
			else:
				print(f"Data incomplete, Charge {charge.id} not marked as pulled.")
	except Exception as e:
		print(f"\nError occurred while getting related data: {e}")

