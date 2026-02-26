from sqlmodel import Session, create_engine, select, func
from models import Movie
from datetime import date, timedelta

engine = create_engine("sqlite:///boxoffice.db")
session = Session(engine)

today = date.today()
week_start = today - timedelta(days=7)
month_start = today.replace(day=1)

print(f"Today: {today}")
print(f"Week Start: {week_start}")

# Check raw dates in DB
print("\n--- Sample Release Dates ---")
movies = session.exec(select(Movie).where(Movie.release_date != None).limit(5)).all()
for m in movies:
    print(f"ID: {m.id}, Name: {m.name}, Date: {m.release_date} (Type: {type(m.release_date)})")

# Test 1: Compare using STRINGS
print("\n--- Test 1: String Comparison ---")
week_start_str = week_start.strftime("%Y-%m-%d")
today_str = today.strftime("%Y-%m-%d")
try:
    count_str = session.exec(
        select(func.count(Movie.id))
        .where(Movie.release_date >= week_start_str)
        .where(Movie.release_date <= today_str)
    ).first()
    print(f"String Query Count: {count_str}")
except Exception as e:
    print(f"String Query Failed: {e}")

# Test 2: Compare using DATE OBJECTS
print("\n--- Test 2: Date Object Comparison ---")
try:
    count_date = session.exec(
        select(func.count(Movie.id))
        .where(Movie.release_date >= week_start)
        .where(Movie.release_date <= today)
    ).first()
    print(f"Date Query Count: {count_date}")
except Exception as e:
    print(f"Date Query Failed: {e}")
