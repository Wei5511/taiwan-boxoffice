from sqlmodel import Session, select
from database import engine
from models import Movie, WeeklyBoxOffice

def verify_data():
    with Session(engine) as session:
        # Check counts
        movie_count = session.exec(select(Movie)).all()
        record_count = session.exec(select(WeeklyBoxOffice)).all()
        
        print(f"Total Movies: {len(movie_count)}")
        print(f"Total Weekly Records: {len(record_count)}")
        
        # Check first 5 records
        print("\nSample Data (First 5):")
        print("-" * 100)
        statement = select(WeeklyBoxOffice).limit(5)
        results = session.exec(statement).all()
        
        for record in results:
            movie = record.movie
            print(f"Movie: {movie.name} ({movie.country})")
            print(f"  Release Date: {movie.release_date}")
            print(f"  Report Date: {record.report_date_start} to {record.report_date_end}")
            print(f"  Revenue: ${record.weekly_revenue:,} (Tickets: {record.weekly_tickets:,})")
            print(f"  Theaters: {record.theater_count}")
            print("-" * 50)

if __name__ == "__main__":
    verify_data()
