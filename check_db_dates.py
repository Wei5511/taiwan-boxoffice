from sqlmodel import Session, select
from models import WeeklyBoxOffice
from database import engine
from sqlalchemy import func

def check_dates():
    with Session(engine) as session:
        statement = select(
            WeeklyBoxOffice.report_date_start, 
            WeeklyBoxOffice.report_date_end
        ).distinct().order_by(WeeklyBoxOffice.report_date_start)
        
        results = session.exec(statement).all()
        
        print("Available Date Ranges in Database:")
        for start, end in results:
            print(f"{start} to {end}")

if __name__ == "__main__":
    check_dates()
