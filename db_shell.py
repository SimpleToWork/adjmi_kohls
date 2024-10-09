import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Charge, AuditIssue, AuditTrouble, Document, Email, FillDetail, PoReceiver, Report, RoutingRequest1, RoutingRequest2
import code


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=True)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


engine, session = setup_database()


def drop_all_data():
	try:
		for table in reversed(Base.metadata.sorted_tables):
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


# running this script (python db_shell.py) creates a python shell with the proper imports to interact with the DB
code.interact(local=locals())