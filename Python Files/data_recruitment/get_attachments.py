import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from csv_scraper import setup_driver, login, scrape_attachments, downloads_dir
from data_import.main import setup_database
from data_import.models import Attachment, Document, Report
import requests
import time
import os
from urllib.parse import urlparse, parse_qs


def get_non_downloaded_attachments(session):
	print(f"\nGetting non-downloaded Attachments...")
	attachments = session.query(Attachment).filter_by(downloaded=False).all()
	if len(attachments) > 0:
		print(f"\nFound {len(attachments)} Attachments: {attachments}")
	else:
		print(f"No non-downloaded Attachments found.")
	return attachments


def relate_attachment(session, attachment):
	potential_document = session.query(Document).filter_by(document_name=attachment.filename, charge_number=attachment.charge_number).first()
	potential_report = session.query(Report).filter_by(file_name=attachment.filename, charge_number=attachment.charge_number).first()

	if potential_document:
		print(f"Relating Attachment to Document {potential_document}...")
		attachment.document_id = potential_document.id
	elif potential_report:
		print(f"Relating Attachment to Report {potential_report}...")
		attachment.report_id = potential_report.id
	else:
		print(f"No matching records found.")


def get_attachments_process(session, driver):
	attachments_to_download = get_non_downloaded_attachments(session)

	for attachment in attachments_to_download:
		download_path = os.path.join(downloads_dir, 'attachments')
		new_file_path = scrape_attachments(driver, download_path, attachment.link, attachment.filename)
		if new_file_path:
			attachment.downloaded = True
			attachment.file_path = new_file_path
			print(f"Marking Attachment as downloaded...")
			relate_attachment(session, attachment)
			session.commit()
			print(f"Done: {attachment}")
		else:
			continue


if __name__ == '__main__':
	engine, session = setup_database()

	attachments_to_download = get_non_downloaded_attachments(session)

	driver = setup_driver()
	login(driver)

	for attachment in attachments_to_download:
		download_path = os.path.join(downloads_dir, 'attachments')
		new_file_path = scrape_attachments(driver, download_path, attachment.link, attachment.filename)
		if new_file_path:
			attachment.downloaded = True
			attachment.file_path = new_file_path
			print(f"Marking Attachment as downloaded...")
			relate_attachment(session, attachment)
			session.commit()
			print(f"Done: {attachment}")
		else:
			continue

