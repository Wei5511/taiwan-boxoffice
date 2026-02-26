"""
Taiwan Box Office Historical Data Backfill Script
Fetches weekly box office data directly from the TFI API using Playwright.
"""

import os
import time
import json
from datetime import datetime, date, timedelta
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select
from models import Movie, WeeklyBoxOffice
from database import engine, create_db_and_tables

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

def save_api_data_to_database(api_response):
    """
    Save API response data to SQLite database
    """
    if not api_response or 'data' not in api_response:
        return 0
    
    data = api_response['data']
    items = data.get('dataItems', [])
    
    # Parse report dates
    try:
        start_str = data.get('start', '').split('T')[0]
        end_str = data.get('end', '').split('T')[0]
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except Exception as e:
        print(f"  Error parsing dates: {e}")
        return 0
        
    create_db_and_tables()
    
    records_saved = 0
    records_skipped = 0
    
    with Session(engine) as session:
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
                
                # Get or Create Movie
                statement = select(Movie).where(Movie.name == name)
                results = session.exec(statement)
                movie = results.first()
                
                if not movie:
                    # FIX: Clean country name
                    country = item.get('region')
                    if country == "中華民國":
                        country = "台灣"

                    movie = Movie(
                        name=name,
                        release_date=release_date,
                        country=country,
                        distributor=item.get('publisher')
                    )
                    session.add(movie)
                    session.commit()
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
                    weekly_tickets=clean_int(item.get('tickets')),
                    cumulative_tickets=clean_int(item.get('totalTickets'))
                )
                session.add(weekly_record)
                records_saved += 1
            
            except Exception as e:
                print(f"  Error processing movie {name}: {e}")
                continue
        
        session.commit()
    
    print(f"  ✓ {start_date} to {end_date}: Saved {records_saved} records, skipped {records_skipped}")
    return records_saved

def get_monday(d):
    """Return the Monday of the week for a given date"""
    return d - timedelta(days=d.weekday())

def scrape_historical_boxoffice_data(start_year=2016, weeks_to_scrape=None):
    """
    Scrape historical box office reports via API (2016 - Present)
    """
    
    api_base_url = "https://boxofficetw.tfai.org.tw/stat/qsl"
    
    print(f"台灣電影歷史票房數據爬蟲 (API版)")
    print(f"年份: {start_year} - 至今")
    print("="*80)
    
    total_records_saved = 0
    
    # Generate list of dates (Mondays)
    today = date.today()
    current_date = get_monday(today)
    
    target_date = date(start_year, 1, 1)
    target_monday = get_monday(target_date)
    
    dates_to_scrape = []
    
    # We go backwards from current week to target year
    d = current_date
    while d >= target_monday:
        dates_to_scrape.append(d)
        d -= timedelta(days=7)
        
    if weeks_to_scrape:
        dates_to_scrape = dates_to_scrape[:weeks_to_scrape]
        
    print(f"預計處理 {len(dates_to_scrape)} 週數據")
    
    try:
        with sync_playwright() as p:
            print("\n正在啟動瀏覽器...")
            browser = p.chromium.launch(
                headless=False, # Headless=False helps bypass some bot protections
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()
            
            # 1. Visit main page to establish session/cookies
            print(f"正在建立連線 Session...")
            page.goto("https://boxofficetw.tfai.org.tw/statistic", wait_until='networkidle')
            time.sleep(3)
            
            for idx, week_start in enumerate(dates_to_scrape):
                date_str = week_start.strftime('%Y-%m-%d')
                print(f"\n[{idx+1}/{len(dates_to_scrape)}] 正在下載週次: {date_str} ...")
                
                # Construct API URL
                # qsl?mode=Week&start=2024-01-01&ascending=false&orderedColumn=ReleaseDate&page=0&size=1000&region=all
                api_url = (
                    f"{api_base_url}?"
                    f"mode=Week&"
                    f"start={date_str}&"
                    f"ascending=false&"
                    f"orderedColumn=ReleaseDate&"
                    f"page=0&"
                    f"size=1000&" # Get all movies in one page
                    f"region=all"
                )
                
                try:
                    # Navigate to API URL directly
                    response = page.goto(api_url)
                    
                    # Parse JSON
                    try:
                        api_data = response.json()
                        records = save_api_data_to_database(api_data)
                        total_records_saved += records
                    except json.JSONDecodeError:
                        print(f"  ✗ 無法解析 JSON 回應 (可能被阻擋或無數據)")
                        content = page.content()
                        if "403" in content or "Forbidden" in content:
                            print("  ✗ 403 Forbidden - 需要等待或重試")
                            time.sleep(10)
                    except Exception as e:
                        print(f"  ✗ 處理數據錯誤: {e}")
                        
                except Exception as e:
                    print(f"  ✗ 請求錯誤: {e}")
                
                # Random delay to be polite and avoid blocks
                time.sleep(1) 
            
            browser.close()
            
            print("\n" + "="*80)
            print("✓ 歷史數據下載完成！")
            print(f"總共新增記錄: {total_records_saved}")
            
            # Summary
            with Session(engine) as session:
                movie_count = len(list(session.exec(select(Movie)).all()))
                record_count = len(list(session.exec(select(WeeklyBoxOffice)).all()))
                print(f"資料庫總計: {movie_count} 部電影, {record_count} 筆週票房記錄")
            print("="*80)
            
    except Exception as e:
        print(f"\n✗ 嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Scrape from 2016-2026
    start_year = 2016
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        scrape_historical_boxoffice_data(start_year=2026, weeks_to_scrape=2)
    else:
        scrape_historical_boxoffice_data(start_year=start_year)
