import os
import sys
import time
from datetime import datetime
import psycopg2
from sqlmodel import Session, select, create_engine, SQLModel

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Movie, WeeklyBoxOffice
from database import engine as default_engine, create_db_and_tables
from playwright.sync_api import sync_playwright

def get_fallback_engine():
    """Provides an IPv4 fallback engine since local Windows lacks IPv6 for Supabase direct connect"""
    def get_conn():
        return psycopg2.connect(
            host="aws-0-ap-northeast-1.pooler.supabase.com",
            port=6543,
            user="postgres.ufiwrwbfbxyqamkikpia",
            password="Wei03230501!",
            database="postgres",
            sslmode="require",
            options="-c supavisor_session_id=main"
        )
    return create_engine("postgresql+psycopg2://", creator=get_conn, echo=False)

def import_data():
    # 1. Database Connection Check
    try:
        with default_engine.connect() as conn:
            print("Successfully connected using default engine from database.py.")
            engine = default_engine
    except Exception as e:
        print("Default engine connection failed (likely IPv6 DNS error).")
        print("Falling back to IPv4 Pooler strictly for data injection...")
        engine = get_fallback_engine()
        
    SQLModel.metadata.create_all(engine)
    
    # 2. Fetch Data
    url = "https://boxofficetw.tfai.org.tw/stat/qsl?mode=Week&start=2020-02-17&ascending=false&orderedColumn=ReleaseDate&page=0&size=1000&region=all"
    
    print("Launching headless browser to bypass TFIA Cloudflare...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        print("Establishing session cookies...")
        page.goto("https://boxofficetw.tfai.org.tw/statistic", wait_until='networkidle')
        time.sleep(3)
        
        print(f"Fetching actual JSON data: {url}")
        res = page.goto(url)
        time.sleep(2)
        
        try:
            data = res.json()
        except:
            print("Failed to parse JSON")
            browser.close()
            return
            
        browser.close()
        
    # 3. Parse Data
    items = data.get('data', {}).get('dataItems', [])
    if not items:
        if 'dataItems' in data: items = data['dataItems']
        elif isinstance(data, list): items = data
    
    start_str = data.get('data', {}).get('start', '2020-02-17').split('T')[0]
    end_str = data.get('data', {}).get('end', '2020-02-23').split('T')[0]
    
    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    
    print(f"Found {len(items)} movies for week {start_str} to {end_str}. Inserting...")
    
    # 4. Insert into Database
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
        print(f"✅ Insertion complete! Added {records_saved} new WeeklyBoxOffice records to Supabase.")

if __name__ == '__main__':
    import_data()
