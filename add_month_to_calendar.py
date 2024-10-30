from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Calendar
from datetime import datetime, timedelta


def setup_database():
	connection_string = "mysql+mysqlconnector://root:Simple123@localhost/adjmi_kohls"
	engine = create_engine(connection_string, echo=False)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()
	return engine, session


engine, session = setup_database()


def current_month_to_calendar():
	today = datetime.today()
	year = today.year
	month = today.month

	existing_entry = session.query(Calendar).filter_by(year=year, month=month).first()
	if existing_entry:
		print(f"Calendar instance for current month ({month}-{year}) already exists")
		return

	start_date = datetime(year, month, 1)
	end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

	new_calendar = Calendar(
		year=year,
		month=month,
		start_date=start_date,
		end_date=end_date
	)
	session.add(new_calendar)
	session.commit()
	print(f"Added current month ({month}-{year}) to Calendar: {new_calendar}")


if __name__ == '__main__':
	try:
		print("Attempting to add current month to Calendar...")
		current_month_to_calendar()
	except Exception as e:
		print(f"Error Occurred while trying to add to Calendar: {e}")
	finally:
		session.close()