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


# Adds current month to Calendar table
def current_month_to_calendar():
    # Get current day, month, year
    today = datetime.today()
    year = today.year
    month = today.month

    # Check if current month, year already exists in Calendar table, if so, do not add it
    existing_entry = session.query(Calendar).filter_by(year=year, month=month).first()
    if existing_entry:
        print(f"Calendar instance for current month ({month}-{year}) already exists")
        return

    # Calculate first and last day of current month
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Create new Calendar instance (pulled and imported boolean fields default to False)
    new_calendar = Calendar(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date
    )
    session.add(new_calendar)
    session.commit()
    print(f"Added current month ({month}-{year}) to Calendar: {new_calendar}")


def add_past_n_years(years):
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    months = years * 12
    for i in range(1, months + 1):
        # Calculate target month and year
        month = current_month - i
        year = current_year

        # Adjust month and year if month goes below 1 (January)
        while month < 1:
            month += 12
            year -= 1

        # Skip if the calculated date goes beyond the specified range
        if year < current_year - years:
            break

        # Check if the entry already exists
        existing_entry = session.query(Calendar).filter_by(year=year, month=month).first()
        if existing_entry:
            print(f"Calendar instance for {month}-{year} already exists.")
            continue

        # Calculate start and end dates for the month
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Add new Calendar instance
        new_calendar = Calendar(
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date
        )
        session.add(new_calendar)
        print(f"Added {month}-{year} to Calendar: {new_calendar}")

    session.commit()
    print(f"\nPast {years} years added to Calendar.")


if __name__ == '__main__':
    try:
        print("Attempting to add current month to Calendar...")
        add_past_n_years(2)
        current_month_to_calendar()
    except Exception as e:
        print(f"Error Occurred while trying to add to Calendar: {e}")
    finally:
        session.close()
