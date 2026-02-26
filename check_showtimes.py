
from sqlmodel import Session, select, create_engine, func
from models import DailyShowtime

sqlite_file_name = "boxoffice.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

with Session(engine) as session:
    count = session.exec(select(func.count(DailyShowtime.id))).one()
    print(f"Total DailyShowtime records: {count}")
    
    if count > 0:
        print("\nSample records:")
        records = session.exec(select(DailyShowtime).limit(5)).all()
        for r in records:
            print(r)
