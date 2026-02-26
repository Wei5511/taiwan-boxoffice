from sqlmodel import Session, create_engine, select, delete
from models import DailyShowtime

engine = create_engine("sqlite:///boxoffice.db")

with Session(engine) as session:
    print("Checking for Mojibake...")
    # Find rows with bad encoding
    statement = select(DailyShowtime).where(DailyShowtime.region.like('%å%'))
    bad_rows = session.exec(statement).all()
    
    count = len(bad_rows)
    print(f"Found {count} rows with Mojibake.")
    
    if count > 0:
        print("Deleting bad rows...")
        for row in bad_rows:
            session.delete(row)
        session.commit()
        print("✅ Deleted bad rows.")
    else:
        print("✅ No bad rows found.")
