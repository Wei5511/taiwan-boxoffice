"""
Yahoo Movies Taiwan Scraper
Scrapes daily showtime counts using Playwright
"""

import time
from datetime import date, datetime
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import Movie, DailyShowtime

def scrape_yahoo_showtimes():
    print("Yahoo Movies Showtimes Scraper (Playwright Version)")
    print("="*80)
    
    create_db_and_tables()
    today = date.today()
    print(f"Date: {today}")
    
    with sync_playwright() as p:
        print("\nStarting browser...")
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-TW',
            timezone_id='Asia/Taipei'
        )
        
        # Hide webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        
        # 1. Get Movie List
        url = "https://movies.yahoo.com.tw/movietime.html"
        print(f"Fetching movie list from: {url}")
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for content
            try:
                page.wait_for_selector('.release_movie_name', timeout=5000)
            except:
                print("⚠ Warning: '.release_movie_name' not found immediately. Checking page content...")
                if 'yahoo' not in page.url:
                    print(f"❌ Redirected to unexpected URL: {page.url}")
                    browser.close()
                    return

            movies_found = []
            movie_elements = page.locator('.release_info_text').all()
            
            print(f"Found {len(movie_elements)} movie elements.")

            if len(movie_elements) == 0:
                print("⚠ Zero movies found. Saving debug info...")
                page.screenshot(path='yahoo_debug.png')
                with open('yahoo_playwright_debug.html', 'w', encoding='utf-8') as f:
                    f.write(page.content())
                print(f"Page Title: {page.title()}")
                print(f"Current URL: {page.url}")
            
            for item in movie_elements:
                try:
                    name_link = item.locator('.release_movie_name a').first
                    en_name_link = item.locator('.en a').first
                    
                    if name_link.count() > 0:
                        name = name_link.inner_text().strip()
                        href = name_link.get_attribute('href')
                        
                        # Extract Yahoo ID
                        # https://movies.yahoo.com.tw/movieinfo_main/%E7%89%87%E5%90%8D-id
                        yahoo_id = None
                        if href:
                            parts = href.split('-')
                            if parts:
                                yahoo_id = parts[-1]
                        
                        if name and yahoo_id:
                            movies_found.append({
                                'name': name,
                                'yahoo_id': yahoo_id,
                                'url': href
                            })
                except Exception as e:
                    print(f"Error parsing movie item: {e}")
                    continue
            
            print(f"Successfully extracted {len(movies_found)} movies.")
            
            stats = {
                'scraped': len(movies_found),
                'matched': 0,
                'saved': 0
            }
            
            # Process Movies
            with Session(engine) as session:
                for yahoo_movie in movies_found:
                    # Match DB
                    statement = select(Movie).where(Movie.name == yahoo_movie['name'])
                    db_movie = session.exec(statement).first()
                    
                    if not db_movie:
                        # Try partial match or normalization if needed?
                        # For now, strict match as requested
                        continue
                    
                    print(f"Processing '{yahoo_movie['name']}' (ID: {db_movie.id})...")
                    stats['matched'] += 1
                    
                    # Regions to check
                    regions = {
                        "Taipei": 0,    # 台北市
                        "New Taipei": 1, # 新北市
                        "Taoyuan": 2,   # 桃園
                        "Hsinchu": 3,   # 新竹
                        "Taichung": 5,  # 台中
                        "Tainan": 10,   # 台南
                        "Kaohsiung": 11 # 高雄
                    }
                    
                    total_count = 0
                    
                    for region_name, region_id in regions.items():
                        showtime_url = f"https://movies.yahoo.com.tw/movietime_result/{yahoo_movie['yahoo_id']}/{region_id}"
                        
                        try:
                            # Visit showtime page
                            # Don't need full load, just DOM
                            page.goto(showtime_url, wait_until='domcontentloaded', timeout=30000)
                            
                            # Count showtimes
                            # Selector: ul.area_time_list -> li -> label
                            # Or simpler: .area_time_list label
                            # Yahoo structure: each showtime is a label or inside a label
                            
                            # Check if "查無場次" exists
                            no_show = page.locator('text=查無場次').count() > 0
                            if no_show:
                                continue
                                
                            # Count time labels
                            # Yahoo uses <label> for time selection inside the list
                            # Structure: <ul class="area_time_list"> <li> <label> ... </label> </li> </ul>
                            count = page.locator('.area_time_list label').count()
                            
                            if count > 0:
                                record = DailyShowtime(
                                    movie_id=db_movie.id,
                                    date=today,
                                    region=region_name,
                                    showtime_count=count
                                )
                                session.add(record)
                                total_count += count
                                stats['saved'] += 1
                                # print(f"  {region_name}: {count}")
                                
                        except Exception as e:
                            print(f"  Error fetching {region_name}: {e}")
                            
                    session.commit()
                    if total_count > 0:
                        print(f"  Saved {total_count} showtimes.")
                        
        except Exception as e:
            print(f"Global Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
            
    print("="*80)
    print(f"Summary: Scraped {stats['scraped']} movies. Matched {stats['matched']}. Saved {stats['saved']} records.")
    print("="*80)

if __name__ == "__main__":
    scrape_yahoo_showtimes()
