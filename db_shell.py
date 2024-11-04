import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
	Base,
	Calendar,
	Charge,
	AuditIssue,
	AuditTrouble,
	Document,
	Email,
	FillDetail,
	PoReceiver,
	Report,
	RoutingRequest1,
	RoutingRequest2,
	Dispute
)
import code
from datetime import datetime, timedelta


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


engine, session = setup_database()


def drop_all_data():
	try:
		for table in reversed(Base.metadata.sorted_tables):
			if table.name != 'calendar':
				session.execute(table.delete())
				print(f"Dropped all data from {table.name}")

		session.commit()
		print("All data dropped successfully from all tables")
	except Exception as e:
		print(f"An error occurred: {e}")
		session.rollback()
	finally:
		session.close()


def query_all(table):
	return session.query(table).all()


def query_by(table, field, value):
	column = getattr(table, field, None)
	if column is None:
		raise AttributeError(f"{table.__name__} has no column '{field}'")

	return session.query(table).filter(column == value).all()


def new_calendar(year, month, pulled=False):
	start_date = datetime(year, month, 1)
	end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

	calendar = Calendar(
		year=year,
		month=month,
		start_date=start_date,
		end_date=end_date,
		pulled=pulled
	)
	session.add(calendar)
	session.commit()
	print(f"Added new Calendar instance: {calendar}")


# running this script (python db_shell.py) creates a python shell with the proper imports/methods to interact with the DB
try:
	code.interact(local=locals())
finally:
	session.close()
	print("Session closed.")