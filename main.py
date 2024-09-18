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
	# Wait for the table to be present
	table = wait_for_element(
		By.XPATH,
		'/html/body/router-view/main-layout/div/main/div/div[2]/div[2]/div[2]/div[2]/div/data-table/div[5]/table',
	)

	# Find all rows in the table
	rows = table.find_elements(By.XPATH, './/tbody/tr')  # Assuming tbody is where the rows are

	# Extract the text from spans within the 3rd td of each row
	charge_numbers = []
	for row in rows:
		try:
			# Get the span in the 3rd td of the row
			span = row.find_element(By.XPATH, './/td[3]/data-table-cell/a/span')
			charge_numbers.append(span.text)
		except Exception as e:
			print(f"Error extracting span text: {e}")

	# Print the extracted data
	print(f" \n data: {charge_numbers} \n")
	return charge_numbers


def scrape_charge_data(charge):
	data = {}
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

	return data


def export_to_csv():
	button = wait_for_element(
		By.XPATH,
		'//*[@id="content"]/div/div[2]/div[2]/div[2]/div[2]/div/data-table/div[2]/div[2]/div/div/a[3]',
		EC.element_to_be_clickable
	)
	button.click()


def run_process():
	login()
	navigate_to_charges()
	fill_search_criteria('09/01/2024', '09/30/2024')
	charge_number = get_charge_numbers()
	charge_data = []
	for index, charge in enumerate(charge_number):
		if index == 6:
			break
		data = scrape_charge_data(charge)
		charge_data.append(data)
	print(charge_data)


if __name__ == "__main__":
	try:
		run_process()
		input('Press enter to close...')
	except Exception as e:
		print(f"An Error Occurred: {e}")
	finally:
		driver.quit()
