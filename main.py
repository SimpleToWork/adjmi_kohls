from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import os

chrome_options = Options()
download_dir = os.path.join(os.getcwd(), "downloads")
chrome_options.add_experimental_option("prefs", {
	"download.default_directory": download_dir,
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


def wait_for_element(by, value, condition=EC.presence_of_element_located, timeout=30):
	return WebDriverWait(driver, timeout).until(condition((by, value)))


def login():
	username_input = wait_for_element(By.ID, "username")
	username_input.send_keys("Kohlscompliance@adjmi-apparel.com")

	password_input = wait_for_element(By.ID, "password")
	password_input.send_keys("Miracleyvon24*")

	login_button = wait_for_element(By.CSS_SELECTOR, 'a.btn.btn-primary.btn-block.btn-lg', EC.element_to_be_clickable)
	login_button.click()


def navigate_to_charges():
	vendor_tools = wait_for_element(By.CSS_SELECTOR, 'a[href="#mm-item-2"]', EC.element_to_be_clickable)
	vendor_tools.click()

	find_charges = wait_for_element(By.CSS_SELECTOR, 'a[href="#/search/charge"]', EC.element_to_be_clickable, 10)
	find_charges.click()


def fill_search_criteria(start, end):
	start_date = wait_for_element(By.ID, 'datecontrol_filter_date_null_103_undefined')
	start_date.send_keys(start)

	end_date = wait_for_element(By.ID, 'datecontrol_filter_date_stop_null_105_undefined')
	end_date.send_keys(end)
	end_date.send_keys(Keys.ESCAPE)

	# Ensure the button is visible and clickable
	search_button = wait_for_element(By.CSS_SELECTOR, 'button.btn.btn-primary.btn-lg', EC.visibility_of_element_located)
	# Scroll into view if necessary (optional)
	driver.execute_script("arguments[0].scrollIntoView();", search_button)

	# Click the button
	wait_for_element(By.CSS_SELECTOR, 'button.btn.btn-primary.btn-lg', EC.element_to_be_clickable).click()


def get_charge_numbers():
	charge_numbers = []

	try:
		print("Waiting for the table to load...")
		# Wait for the table to be visible (not just present)
		table = wait_for_element(
			By.XPATH,
			'/html/body/router-view/main-layout/div/main/div/div[2]/div[2]/div[3]/div[2]/div/data-table/div[5]/table',
			EC.visibility_of_element_located,
			timeout=60
		)

		if table is None:
			print("Table not found.")
			return charge_numbers

		print("Table found, waiting for rows...")

		# Wait for rows to be present and visible
		rows = table.find_elements(By.XPATH, './/tbody/tr')

		if len(rows) == 0:
			print("No rows found in the table.")
			return charge_numbers

		print(f"Found {len(rows)} rows in the table.")

		# Print the inner HTML of the table for debugging
		print("Table HTML:")
		print(table.get_attribute('innerHTML'))

		# Extract charge numbers from the rows
		for index, row in enumerate(rows):
			try:
				# Get the span in the 3rd td of the row
				span = row.find_element(By.XPATH, './/td[3]/data-table-cell/a/span')
				charge_number = span.text
				charge_numbers.append(charge_number)
				print(f"Row {index + 1}: Found charge number {charge_number}")
			except Exception as e:
				print(f"Error extracting charge number from row {index + 1}: {e}")

	except Exception as e:
		print(f"Error while getting charge numbers: {e}")

	print(f"Extracted {len(charge_numbers)} charge numbers.")
	return charge_numbers


def export_to_csv():
	button = wait_for_element(
		By.XPATH,
		'//*[@id="content"]/div/div[2]/div[2]/div[2]/div[2]/div/data-table/div[2]/div[2]/div/div/a[3]',
		EC.element_to_be_clickable
	)
	button.click()


def scrape_charge_data(charge):
	data = {"id": charge}
	# go to charge details page
	url = f"https://kss.traversesystems.com/#/inquiry/charge?keyNum={charge}"
	driver.get(url)

	time.sleep(0.5)

	WebDriverWait(driver, 10).until(
		EC.url_contains(f"keyNum={charge}")
	)
	wait_for_element(By.ID, 'numerictextbox_charge_num_null_162_undefined')

	data["total_charge"] = wait_for_element(By.ID, 'currencytextbox_charge_dollars_null_357_undefined').get_attribute("value")
	data["charge_type"] = wait_for_element(By.XPATH, '//*[@id="combobox_charge_type_null_23_undefined--container"]/div[2]/input').get_attribute("value")
	data["service_fee"] = wait_for_element(By.ID, 'currencytextbox_service_fee_null_230_undefined').get_attribute("value")
	data["rule_number"] = wait_for_element(By.ID, 'textbox_cust_rule_num_null_174_undefined').get_attribute("value")
	data["rule_description"] = wait_for_element(By.ID, 'textbox_description_null_221_undefined').get_attribute("value")
	data["rcms_rule_number"] = wait_for_element(By.ID, 'textbox_rule_num_null_224_undefined').get_attribute("value")
	data["vendor_number"] = wait_for_element(By.ID, 'textbox_vendor_num_null_262_undefined').get_attribute("value")
	data["vendor_name"] = wait_for_element(By.ID, 'textbox_vendor_name_null_261_undefined').get_attribute("value")
	data["purchase_order"] = wait_for_element(By.ID, 'textbox_po_num_null_206_undefined').get_attribute("value")
	data["charge_location"] = wait_for_element(By.ID, 'textbox_audit_site_null_163_undefined').get_attribute("value")
	data["charge_source"] = wait_for_element(By.ID, 'textbox_source_description_null_363_undefined').get_attribute("value")
	data["deduction_date"] = wait_for_element(By.ID, 'datecontrol_xmit_ap_ts_null_126_undefined').get_attribute("value")
	data["charge_tier"] = wait_for_element(By.ID, 'textbox_tier_null_238_undefined').get_attribute("value")
	data["charge_comments"] = wait_for_element(By.ID, 'memoedit_audit_comments_null_132_undefined').get_attribute("value")

	time.sleep(0.5)
	related_data = scrape_related_info(charge)
	data["related_data"] = related_data
	return data


def scrape_related_info(charge):
	related_data = {}
	# Wait for the tabs list to be present
	tabs_list = wait_for_element(By.CSS_SELECTOR, 'ul.nav.nav-tabs')

	# Find all tabs initially
	tabs = tabs_list.find_elements(By.CSS_SELECTOR, 'a.au-target')

	for index, _ in enumerate(tabs):
		# Re-locate the tabs in each loop iteration to avoid stale element issues
		tabs_list = wait_for_element(By.CSS_SELECTOR, 'ul.nav.nav-tabs')
		tabs = tabs_list.find_elements(By.CSS_SELECTOR, 'a.au-target')

		# Wait until the current tab is clickable before proceeding
		tab = tabs[index]  # Ensure we're clicking the correct tab in the current loop
		wait_for_element(By.CSS_SELECTOR, 'a.au-target', EC.element_to_be_clickable)

		tab_name = tab.text
		print(f"Clicking on tab: {tab_name}")
		related_data[tab_name] = []
		# Click the tab
		tab.click()

		# Wait for the content under the tab to load
		tab_content_div = wait_for_element(
			By.XPATH,
			f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index + 1}]',
			EC.visibility_of_element_located
		)
		tab_table = wait_for_element(
			By.XPATH,
			f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index + 1}]/tab-data-tables',
			EC.visibility_of_element_located
		)

		try:
			no_result = wait_for_element(By.XPATH,
			                             f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index + 1}]/tab-data-tables/div/div[1]/div',
			                             timeout=1)
			print('no results \n')
			continue
		except Exception as e:
			pass

		try:
			if tab_name not in ['Fill Detail', 'PO Receivers', 'Routing Requests']:
				table = wait_for_element(
					By.XPATH,
					f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index + 1}]/tab-data-tables/div/div[1]/data-table/div[4]/table',
					timeout=3
				)
			else:
				table = wait_for_element(
					By.XPATH,
					f'/html/body/router-view/main-layout/div/main/div/div[2]/tab-container/div/div[2]/div/div/div/div[{index + 1}]/tab-data-tables/div/div[1]/data-table/div[5]/table',
					timeout=3
				)
			print('results found, scraping...')
			table_headers = table.find_element(By.XPATH, './/thead[2]')
			column_names = table_headers.find_elements(By.TAG_NAME, 'a')
			table_rows = tab_table.find_elements(By.TAG_NAME, 'tbody')
			for row in table_rows:
				spans = row.find_elements(By.TAG_NAME, 'span')
				formatted_data = {}
				for i, data in enumerate(spans):
					formatted_data[column_names[i].text] = data.text

				related_data[tab_name].append(formatted_data)

		except Exception as e:
			print(f"Error scraping table {e}")

	# print(related_data)
	return related_data


def run_process():
	try:
		login()
		navigate_to_charges()
		fill_search_criteria('09/01/2024', '09/30/2024')
		charge_numbers = get_charge_numbers()
		print(charge_numbers)
		charge_data = []
		for index, charge in enumerate(charge_numbers):
			if index == 3:
				break
			data = scrape_charge_data(charge)
			charge_data.append(data)
		print(charge_data)
	except Exception as e:
		print(f"error occurred: {e}")


if __name__ == "__main__":
	try:
		run_process()
		input('Press enter to close...')
	except Exception as e:
		print(f"An Error Occurred: {e}")
	finally:
		driver.quit()
