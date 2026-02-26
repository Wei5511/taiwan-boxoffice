
import os
import time
import json
import traceback
from datetime import datetime, date, timedelta
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select
from models import Movie, WeeklyBoxOffice
from database import engine, create_db_and_tables

# ANSI Colors for visible feedback
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def clean_int(val):
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(float(val.replace(',', '').replace(' ', '')))
        except:
            return 0
    return 0

def save_api_data_to_database(api_response, session):
    """
    Save API response data to SQLite database using the provided session.
    Returns count of saved records.
    """
    if not api_response or 'data' not in api_response:
        return 0, 0
    
    data = api_response['data']
    items = data.get('dataItems', [])
    
    # Parse report dates
    try:
        start_str = data.get('start', '').split('T')[0]
        end_str = data.get('end', '').split('T')[0]
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except Exception as e:
        print(f"{Colors.FAIL}Error parsing dates: {e}{Colors.ENDC}")
        return 0, 0
        
    records_saved = 0
    records_skipped = 0
    
    for item in items:
        try:
            name = item.get('name')
            if not name:
                continue
                
            # Parse release date
            release_date = None
            rd_str = item.get('releaseDate')
            if rd_str:
                try:
                    release_date = datetime.strptime(rd_str, '%Y-%m-%d').date()
                except:
                    pass
            
            # FIX: Clean country name
            country = item.get('region')
            if country == "中華民國":
                country = "台灣"

            # Get or Create Movie
            # Optimisation: We could cache movies in memory, but for safety let's query
            movie = session.exec(select(Movie).where(Movie.name == name)).first()
            
            if not movie:
                movie = Movie(
                    name=name,
                    release_date=release_date,
                    country=country,
                    distributor=item.get('publisher')
                )
                session.add(movie)
                session.commit() # Commit immediately to get ID
                session.refresh(movie)
            
            # Check if record already exists (duplicate detection)
            existing_record = session.exec(
                select(WeeklyBoxOffice)
                .where(WeeklyBoxOffice.movie_id == movie.id)
                .where(WeeklyBoxOffice.report_date_start == start_date)
                .where(WeeklyBoxOffice.report_date_end == end_date)
            ).first()
            
            if existing_record:
                records_skipped += 1
                continue
            
            # Create Weekly Record
            weekly_record = WeeklyBoxOffice(
                movie_id=movie.id,
                report_date_start=start_date,
                report_date_end=end_date,
                theater_count=clean_int(item.get('theaterCount')),
                weekly_revenue=clean_int(item.get('amount')),
                cumulative_revenue=clean_int(item.get('totalAmount')),
                weekly_tickets=clean_int(item.get('tickets'))
            )
            session.add(weekly_record)
            records_saved += 1
        
        except Exception as e:
            # print(f"  Error processing movie {name}: {e}")
            continue
    
    return records_saved, records_skipped

def get_mondays_of_year(year):
    mondays = []
    d = date(year, 1, 1)
    # Advance to first Monday
    while d.weekday() != 0:
        d += timedelta(days=1)
    
    while d.year == year:
        mondays.append(d)
        d += timedelta(days=7)
    return mondays

def scrape_missing_years():
    print(f"{Colors.HEADER}Starting Rescue Scrape for 2016-2023{Colors.ENDC}")
    create_db_and_tables()
    
    api_base_url = "https://boxofficetw.tfai.org.tw/stat/qsl"
    years = range(2016, 2024) # 2016 to 2023
    
    with sync_playwright() as p:
        print(f"{Colors.BLUE}Launching Browser...{Colors.ENDC}")
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page()
        
        # Initialize Session
        try:
            page.goto("https://boxofficetw.tfai.org.tw/statistic", wait_until='networkidle', timeout=60000)
            time.sleep(2)
        except Exception as e:
            print(f"{Colors.FAIL}Failed to load init page: {e}{Colors.ENDC}")
            return

        with Session(engine) as session:
            total_records_session = 0
            
            for year in years:
                print(f"\n{Colors.HEADER}Processing Year: {year}{Colors.ENDC}")
                mondays = get_mondays_of_year(year)
                
                for idx, monday in enumerate(mondays):
                    week_num = idx + 1
                    date_str = monday.strftime('%Y-%m-%d')
                    print(f"{Colors.BLUE}Importing {year} Week {week_num} ({date_str})...{Colors.ENDC}", end="", flush=True)
                    
                    api_url = (
                        f"{api_base_url}?"
                        f"mode=Week&"
                        f"start={date_str}&"
                        f"ascending=false&"
                        f"orderedColumn=ReleaseDate&"
                        f"page=0&"
                        f"size=1000&"
                        f"region=all"
                    )
                    
                    try:
                        response = page.goto(api_url, timeout=30000)
                        api_data = response.json()
                        
                        saved, skipped = save_api_data_to_database(api_data, session)
                        total_records_session += saved
                        
                        # Commit every 10 weeks or if lots of data
                        if week_num % 10 == 0:
                            session.commit()
                            print(f" {Colors.GREEN}✓ Saved {saved} (Committed){Colors.ENDC}")
                        else:
                            print(f" {Colors.GREEN}✓ Saved {saved}{Colors.ENDC}")
                            
                    except Exception as e:
                        print(f" {Colors.FAIL}Skipping {year} Week {week_num}: {e}{Colors.ENDC}")
                        # Don't crash, just continue
                    
                    # Polite delay
                    time.sleep(0.5)
                
                # Commit at end of year
                session.commit()
                print(f"{Colors.GREEN}Year {year} Completed and Committed.{Colors.ENDC}")
        
        browser.close()
        print(f"\n{Colors.HEADER}Rescue Mission Complete. Total Records Added: {total_records_session}{Colors.ENDC}")

if __name__ == "__main__":
    scrape_missing_years()
