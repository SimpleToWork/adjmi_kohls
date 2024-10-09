import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Charge, AuditIssue, AuditTrouble, Document, Email, FillDetail, PoReceiver, Report, RoutingRequest1, RoutingRequest2
from main import setup_database
import code

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


# running this script (python db_shell.py) creates a python shell with the proper imports to interact with the DB
code.interact(local=locals())