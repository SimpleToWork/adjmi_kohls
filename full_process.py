from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from get_charges import get_charges_process
from import_charges import import_charges_process
from get_related_data import get_related_data_process
from import_related_data import import_related_data_process
from csv_scraper import downloads_dir
from models import Base


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)
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


if __name__ == '__main__':
	engine, session = setup_database()
	driver = setup_driver()

	get_charges_process(session, driver)
	import_charges_process(session)
	get_related_data_process(session, driver)
	import_related_data_process(session)

