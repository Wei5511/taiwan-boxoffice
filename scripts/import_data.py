import os
import sys
import json
import cloudscraper
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Movie, WeeklyBoxOffice
from database import engine, create_db_and_tables
from sqlmodel import Session, select, SQLModel

def import_data():
    print("🚀 Initializing lightweight data injection script...")
    SQLModel.metadata.create_all(engine)
    
    url = "https://boxofficetw.tfai.org.tw/stat/qsl?mode=Week&start=2020-02-17&ascending=false&orderedColumn=ReleaseDate&page=0&size=1000&region=all"
    print(f"📡 Fetching JSON data from TFAI via cloudscraper...")
    
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    res = scraper.get(url, timeout=15)
    
    try:
        data = res.json()
    except Exception as e:
        print(f"❌ Failed to decode JSON (Cloudflare block?). HTTP {res.status_code}")
        print(res.text[:300])
        return

    items = data.get('data', {}).get('dataItems', [])
    if not items:
        if 'dataItems' in data: items = data['dataItems']
        elif isinstance(data, list): items = data
    
    start_str = data.get('data', {}).get('start', '2020-02-17').split('T')[0]
    end_str = data.get('data', {}).get('end', '2020-02-23').split('T')[0]
    
    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    
    print(f"✅ Found {len(items)} movies for week {start_str} to {end_str}. Inserting...")
    
    records_saved = 0
    with Session(engine) as session:
        for item in items:
            name = item.get('name')
            if not name: continue
            
            region = item.get('region')
            if region == "中華民國": region = "台灣"
            
            rd = item.get('releaseDate')
            release_date = None
            if rd:
                try: release_date = datetime.strptime(rd, '%Y-%m-%d').date()
                except: pass
                
            movie = session.exec(select(Movie).where(Movie.name == name)).first()
            if not movie:
                movie = Movie(name=name, release_date=release_date, country=region, distributor=item.get('publisher'))
                session.add(movie)
                session.commit()
                session.refresh(movie)
                
            existing = session.exec(select(WeeklyBoxOffice).where(
                WeeklyBoxOffice.movie_id == movie.id,
                WeeklyBoxOffice.report_date_start == start_date
            )).first()
            
            if not existing:
                record = WeeklyBoxOffice(
                    movie_id=movie.id,
                    report_date_start=start_date,
                    report_date_end=end_date,
                    theater_count=item.get('theaterCount', 0),
                    weekly_revenue=item.get('amount', 0),
                    cumulative_revenue=item.get('totalAmount', 0),
                    weekly_tickets=item.get('tickets', 0),
                    cumulative_tickets=item.get('totalTickets', 0)
                )
                session.add(record)
                records_saved += 1
                
        session.commit()
        print(f"🎉 Insertion complete! Added {records_saved} new WeeklyBoxOffice records to Supabase.")

if __name__ == '__main__':
    import_data()
