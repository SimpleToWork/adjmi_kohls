import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
	NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    InvalidSelectorException
)
import time
import os
import shutil
from datetime import datetime

# Directory where exported CSVs will be saved -- will contain sub-folders representing each tab
downloads_dir = os.path.join(os.getcwd(), "downloads")
# Directory where combined CSV files will be saved -- will contain sub-folders representing each tab
combined_dir = os.path.join(os.getcwd(), "combined_files")

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
	"download.default_directory": downloads_dir,
	"download.prompt_for_download": False,
	"download.directory_upgrade": True,
	"safebrowsing.enabled": True
})
# Set up ChromeDriver using the Service class
service = Service(ChromeDriverManager().install())

# Create the Chrome driver instance using the Service object
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to kohls login page
driver.get("https://kss.traversesystems.com/#/login")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


# Selenium's wait for element method abstracted with defaults
# by=selector type - value=element's selector - condition=what to wait for - timeout=how long to wait
def wait_for_element(by, value, condition=EC.presence_of_element_located, timeout=30):
	return WebDriverWait(driver, timeout).until(condition((by, value)))


# used to change the driver's download location
def set_download_directory(new_directory):
	driver.execute_cdp_cmd("Page.setDownloadBehavior", {
		"behavior": "allow",
		"downloadPath": new_directory
	})


# fill login inputs and submit
def login():
	username_input = wait_for_element(By.ID, "username")
	username_input.send_keys("Kohlscompliance@adjmi-apparel.com")

	password_input = wait_for_element(By.ID, "password")
	password_input.send_keys("Miracleyvon24*")

	login_button = wait_for_element(By.CSS_SELECTOR, 'a.btn.btn-primary.btn-block.btn-lg', EC.element_to_be_clickable)
	login_button.click()


# clicks 'Vendor Tools' menu, then clicks 'Find Charges'
def navigate_to_charges():
	vendor_tools = wait_for_element(By.CSS_SELECTOR, 'a[href="#mm-item-2"]', EC.element_to_be_clickable)
	vendor_tools.click()

	find_charges = wait_for_element(By.CSS_SELECTOR, 'a[href="#/search/charge"]', EC.element_to_be_clickable, 10)
	find_charges.click()


# fill search criteria (currently just start and end date)
def fill_search_criteria(start, end):
	start_date = wait_for_element(By.ID, 'datecontrol_filter_date_null_103_undefined')
	start_date.send_keys(start)

	end_date = wait_for_element(By.ID, 'datecontrol_filter_date_stop_null_105_undefined')
	end_date.send_keys(end)
	# "press" esc key to close date select so that it does not interfere with subsequent steps
	end_date.send_keys(Keys.ESCAPE)

	search_button = wait_for_element(By.CSS_SELECTOR, 'button.btn.btn-primary.btn-lg', EC.visibility_of_element_located)
	# Scroll into view if necessary
	driver.execute_script("arguments[0].scrollIntoView();", search_button)

	# Click the button (reselected to prevent 'stale element' error
	wait_for_element(By.CSS_SELECTOR, 'button.btn.btn-primary.btn-lg', EC.element_to_be_clickable).click()


# export charges as CSV
def export_charges_csv():
	button = wait_for_element(
		By.XPATH,
		'/html/body/router-view/main-layout/div/main/div/div[2]/div[2]/div[3]/div[2]/div/data-table/div[2]/div[2]/div/div/a[3]',
		EC.element_to_be_clickable
	)
	# locate/create subdirectory within 'downloads' to store charges CSV
	charge_directory = os.path.join(downloads_dir, "charge_files")
	if not os.path.exists(charge_directory):
		os.makedirs(charge_directory)

	# change driver's download directory to charge_directory (downloads/charge_files)
	set_download_directory(charge_directory)

	# click the 'export to csv' button that will download the CSV
	button.click()


# wait to confirm file was downloaded to ensure interactions with files can continue
def wait_for_file(download_directory, timeout=30):
	end_time = time.time() + timeout
	while time.time() < end_time:
		files = os.listdir(download_directory)
		csv_files = [f for f in files if f.endswith('.csv')]
		if csv_files:
			latest_csv_files = os.path.join(download_directory, max(csv_files, key=lambda f: os.path.getmtime(os.path.join(download_directory, f))))
			if os.path.isfile(latest_csv_files) and os.path.getsize(latest_csv_files) > 0:
				return latest_csv_files
		time.sleep(1)

	return None


# extract the charge numbers (unique identifier) from the downloaded charges CSV -- returns list
def extract_charges_from_csv(file):
	df = pd.read_csv(file)
	charge_numbers = df["Charge Number"].tolist()
	return charge_numbers


# navigates to charge page using URL params
def scrape_charge_data(charge):
	# place charge number in URL param
	url = f"https://kss.traversesystems.com/#/inquiry/charge?keyNum={charge}"
	# navigate to URL
	driver.get(url)
	time.sleep(0.5)
	# wait until URL contains the param before continuing
	WebDriverWait(driver, 10).until(EC.url_contains(f"keyNum={charge}"))
	# run function to click on and extract related tabs for current charge
	export_related_csvs(charge)


# click on tabs within a charge and extract the data as CSV
def export_related_csvs(charge, retries=3):
	try:
		# Wait for the tabs list to be present
		tabs_list = wait_for_element(By.CSS_SELECTOR, 'ul.nav.nav-tabs')
		tabs = tabs_list.find_elements(By.CSS_SELECTOR, 'a.au-target')
		total_tabs = len(tabs)

		print(f"\nProcessing charge: {charge} | Total tabs found: {total_tabs}\n")

		for index, tab in enumerate(tabs):
			try:
				# Re-locate the tabs in each loop iteration to avoid stale element issues
				tabs_list = wait_for_element(By.CSS_SELECTOR, 'ul.nav.nav-tabs')
				tabs = tabs_list.find_elements(By.CSS_SELECTOR, 'a.au-target')
				tab = tabs[index]

				tab_name = tab.text.strip()
				# there are two tabs called 'Routing Requests' with different data
				if tab_name == 'Routing Requests':
					tab_name = f"{tab_name}_{index+1}"
				print(f"	[{index + 1}/{total_tabs}] Clicking on tab: '{tab_name}'")

				# click tab -- Retry mechanism to avoid stale element or timing issues
				for attempt in range(retries):
					try:
						wait_for_element(By.CSS_SELECTOR, 'a.au-target', EC.element_to_be_clickable)
						tab.click()
						time.sleep(0.5)
						break  # Exit retry loop if successful
					except (StaleElementReferenceException, ElementNotInteractableException, TimeoutException) as e:
						if attempt == retries - 1:
							raise e  # Re-raise after final attempt
						print(f"		- Retry clicking on tab '{tab_name}' (attempt {attempt + 1}/{retries})")
						time.sleep(0.5)

				# check if tab contains "No Results" element and skip tab if so
				try:
					# uses full XPath for element to avoid error with Kohls' show/hide DOM structure
					no_results_alert = driver.find_element(By.XPATH, f"/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index+1}]/tab-data-tables/div/div[1]/div")
					if "No Results" in no_results_alert.text:
						print(f"		- No data found in tab '{tab_name}', skipping export")
						continue  # Skip to the next tab
				except NoSuchElementException:
					pass  # Proceed if "No Results" alert is not found

				# Set up the download directory for the current tab
				tab_directory = os.path.join(downloads_dir, tab_name.replace('/', '_'))
				if not os.path.exists(tab_directory):
					os.makedirs(tab_directory)
					print(f"		- Created directory: {tab_directory}")
				# switch download directory to tab's subdirectory within 'downloads' (downloads/{tab name})
				set_download_directory(tab_directory)
				print(f"		- Download directory set to: {tab_directory}")

				# click 'export to csv' button -- Retry mechanism for finding the export button
				for attempt in range(retries):
					try:
						# uses full XPath for element to avoid error with Kohls' show/hide DOM structure
						export_button = wait_for_element(
							By.XPATH,
							f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index+1}]/tab-data-tables/div/div[1]/data-table/div[2]/div[2]/div/div/a[3]',
							EC.element_to_be_clickable,
							timeout=10
						)
						export_button.click()
						print(f"		- Export button clicked for tab: '{tab_name}'")
						time.sleep(0.5)
						break  # Exit retry loop if successful
					except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
						if attempt == retries - 1:
							raise e  # Re-raise after final attempt
						print(f"		- Retry locating export button in tab '{tab_name}' (attempt {attempt + 1}/{retries})")
						time.sleep(0.5)

				# Wait for the file to be downloaded
				latest_csv_file = wait_for_file(tab_directory)

				if latest_csv_file:
					# rename the file to contain the tab name and the charge number
					new_filename = os.path.join(tab_directory, f"{tab_name.replace('/', '_')}_{charge}.csv")
					shutil.move(latest_csv_file, new_filename)
					print(f"		- File downloaded and renamed to: {new_filename.split('/')[-1]}\n")
				else:
					print(f"		- No CSV file found for tab: '{tab_name}' for charge: '{charge}'\n")

			except (TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException) as tab_error:
				print(f"		! Error: {tab_error} while processing tab '{tab_name}' for charge '{charge}'")
				continue

	except Exception as general_error:
		print(f"Error initiating export for charge '{charge}': {general_error}")


# combine CSVs file in each subdirectory within 'downloads' into one CSV for each tab and store them in 'combined_files'
def combine_csvs(parent_directory, combined_directory):
	for root, dirs, files in os.walk(parent_directory):
		for subdir in dirs:  # for each subdirectory within the parent directory (downloads)
			subfolder_path = os.path.join(root, subdir)
			combined_df = pd.DataFrame()

			# go through each file
			for file in os.listdir(subfolder_path):
				if file.endswith('.csv'):
					file_path = os.path.join(subfolder_path, file)
					try:
						# get contents of original file
						df = pd.read_csv(file_path)

						# if directory is charge_files, do not alter the file's charge numbers column
						if subdir != 'charge_files':
							# extract the charge number from the original file's filename
							charge_number = file.split('_')[-1].replace('.csv', '')
							# add the charge number to the data frame's Charge Number column
							df['Charge Number'] = charge_number
						# add this data frame to the combined data frame
						combined_df = pd.concat([combined_df, df], ignore_index=True)
					except pd.errors.EmptyDataError:
						print(f"Warning: '{file_path}' is empty and will be skipped")
					except Exception as e:
						print(f"Error reading '{file_path}': {e}")
			if not combined_df.empty:
				# find/create subdirectory within 'combined_files' to store combined file -- mimics 'downloads' structure
				subfolder_combined_path = os.path.join(combined_directory, subdir)
				if not os.path.exists(subfolder_combined_path):
					os.makedirs(subfolder_combined_path)

				# name file after tab and add a timestamp
				combined_file_path = os.path.join(subfolder_combined_path, f"{subdir}_combined_{timestamp}.csv")
				combined_df.to_csv(combined_file_path, index=False)
				print(f"Combined CSV saved to {combined_file_path}")
			else:
				print(f"No CSV files found in '{subfolder_path}', skipping combination")


# run full scripting process using above functions
def run_process():
	try:
		login()
		navigate_to_charges()
		fill_search_criteria('09/01/2024', '09/30/2024')
		export_charges_csv()
		latest_csv_file = wait_for_file(os.path.join(downloads_dir, "charge_files"))
		if latest_csv_file:
			charge_numbers = extract_charges_from_csv(latest_csv_file)

			for index, charge in enumerate(charge_numbers):
				# condition and break used for testing on smaller scale
				if index == 10:
					break
				# run function to scrape charge and related data on each charge extracted from charges CSV
				scrape_charge_data(charge)

			print("Scraping done, combining CSVs for each tab...\n")
			# after scraping process is done, combine all individual CSVs into one for each subdirectory within 'downloads'
			combine_csvs(downloads_dir, combined_dir)
		else:
			print('CSV file not found within the specified timeout')
	except Exception as e:
		print(f"error occurred: {e}")


if __name__ == "__main__":
	try:
		run_process()
		# combine_csvs(os.path.join(os.getcwd(), "Routing Requests_12"))
		input("Press enter to close...")
	except Exception as e:
		print(f"an error occurred: {e}")
	finally:
		driver.quit()