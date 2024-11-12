from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from data_recruit.get_charges import get_charges_process
from data_import.import_charges import import_charges_process
from data_recruit.get_related_data import get_related_data_process
from data_import.import_related_data import import_related_data_process
from calendar_setup.add_month_to_calendar import run_calendar_method
from data_recruit.csv_scraper import downloads_dir
from data_import.models import Base


def sql_create_engine(username, password, server, database):
    driver = 'ODBC Driver 18 for SQL Server'
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&trusted_connection=no&encrypt=no"
    )
    # print_color(connection_string)
    # conn = create_engine(connection_string)
    # conn = pyodbc.connect(connection_string)
    return connection_string


def setup_database(connection_string):
	# Initial connection string without specifying a database
	# connection_string_base = "mysql+mysqlconnector://root:Simple123@localhost"
	connection_string_base = connection_string
	engine_base = create_engine(connection_string_base, echo=False)
	# with engine_base.connect() as connection:
	# 	# Check if the database exists
	# 	db_exists = connection.execute(text("SHOW DATABASES LIKE 'adjmi_kohls'")).fetchone()
	# 	# Create the database if it doesn't exist
	# 	if not db_exists:
	# 		connection.execute(text("CREATE DATABASE adjmi_kohls"))

	# Now connect specifically to the adjmi_kohls database
	# connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"\
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)  # This creates tables if they don't exist
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


def setup_driver():
	options = Options()
	options.add_experimental_option("prefs", {
		"download.default_directory": downloads_dir,
		"download.prompt_for_download": False,
		"download.directory_upgrade": True,
		"safebrowsing.enabled": True
	})
	# Set up ChromeDriver using the Service class
	setup_service = Service(ChromeDriverManager().install())

	# Create the Chrome driver instance using the Service object
	web_driver = webdriver.Chrome(service=setup_service, options=options)
	return web_driver


# When this file is executed, it runs all the combined processes for scraping and importing
if __name__ == '__main__':
	# Start DB session to be passed through to all steps
	sql_engine_local_string = sql_create_engine(username='admin', password='Simple123', server='localhost', database='Adjmi_Kohls')
	engine, session = setup_database(sql_engine_local_string)

	# Start web driver to be passed through to all scraping steps
	driver = setup_driver()
	try:
		# Setup Calendar
		run_calendar_method(session)
		# Scrape Charges
		get_charges_process(session, driver)
		# Import Scraped Charges to DB
		import_charges_process(session)
		# Scrape Related Data tabs
		get_related_data_process(session, driver)
		# Import scraped Related Data
		import_related_data_process(session)
	except Exception as e:
		# Most errors are handled within each process
		print(f"Error occurred while running full process: {e}")
	finally:
		# Close the web driver and DB session
		driver.quit()
		session.close()
