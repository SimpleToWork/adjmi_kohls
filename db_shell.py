import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Charge, AuditIssue, AuditTrouble, Document, Email, FillDetail, PoReceiver, Report, RoutingRequest1, RoutingRequest2
from main import setup_database
import code

engine, session = setup_database()

# running this script (python db_shell.py) creates a python shell with the proper imports to interact with the DB
code.interact(local=locals())