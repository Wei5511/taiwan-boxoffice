
import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select, create_engine
from models import Movie, DailyShowtime
from datetime import date
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re

# Disable SSL warnings
warnings.simplefilter('ignore', InsecureRequestWarning)

# Database Setup
sqlite_file_name = "boxoffice.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def get_db_movies(session):
    statement = select(Movie)
    return session.exec(statement).all()

def normalize_name(name):
    """Normalize movie name: remove spaces, years (2024), formats (數位版), etc."""
    if not name:
        return ""
    # Remove (Year) e.g. (2024), (2025)
    name = re.sub(r'\(\d{4}\)', '', name)
    # Remove format info inside parens e.g. (數位版), (IMAX), (中文)
    name = re.sub(r'\(.*?\)', '', name)
    # Remove spaces
    name = name.replace(" ", "").replace("　", "")
    return name.strip()

def find_movie_match(scraped_title, db_movies):
    # 1. Exact Match
    for movie in db_movies:
        if movie.name == scraped_title:
            return movie
            
    # Normalize scraped title
    norm_scraped = normalize_name(scraped_title)
    if not norm_scraped:
        return None
        
    # 2. Fuzzy/Normalized Match
    for movie in db_movies:
        norm_db = normalize_name(movie.name)
        if not norm_db:
            continue
            
        # Check equality of normalized names
        if norm_db == norm_scraped:
            print(f"   ✨ Fuzzy Match: '{scraped_title}' == '{movie.name}'")
            return movie
            
        # Check containment (one matches inside other)
        # Only if length is sufficient to avoid false positives (e.g. "Voice")
        if len(norm_scraped) >= 2 and len(norm_db) >= 2:
            if norm_db in norm_scraped or norm_scraped in norm_db:
                print(f"   ✨ Partial Fuzzy Match: '{scraped_title}' ~= '{movie.name}'")
                return movie
    
    # Debug specific failure
    if "陽光女子" in scraped_title:
        print(f"   ⚠️ '陽光女子合唱團' found in scrap source but failed to match DB.")
        
    return None

def scrape_atmovies():
    print("Starting AtMovies Scraper...")
    base_url = "http://www.atmovies.com.tw"
    list_url = f"{base_url}/movie/now/"
    
    try:
        response = requests.get(list_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
        # CRITICAL FIX: Force UTF-8 encoding to prevent Mojibake (å...)
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching list: {e}")
        return

    movie_links = []
    # Find movie links in the list
    # Structure typically: <div class="filmTitle"><a href="/movie/...">Title</a></div>
    # But let's look for any link with /movie/ID/ pattern
    
    # Based on inspection, links might be like /movie/movie_id/ 
    # Let's find all 'a' tags with href starting with /movie/
    # And typically containing an ID (alphanumeric)
    
    seen_urls = set()
    
    # Using a broader search to confirm structure
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        
        # Filter typical non-movie links
        if href.startswith('/movie/') and len(href) > 8 and text:
            # Avoid general nav links
            if href in ['/movie/', '/movie/new/', '/movie/now/', '/movie/next/', '/movie/next2/']:
                continue
            
            # Basic validation: /movie/ID/
            parts = href.strip('/').split('/')
            if len(parts) >= 2: # movie, id
                 if href not in seen_urls:
                    movie_links.append((text, href))
                    seen_urls.add(href)

    print(f"Found {len(movie_links)} unique movie links.")

    stats = {
        'scraped': 0,
        'matched': 0,
        'showtimes_recorded': 0
    }

    with Session(engine) as session:
        db_movies = get_db_movies(session)
        print(f"Loaded {len(db_movies)} movies from DB for matching.")
        
        for title, rel_url in movie_links:
            stats['scraped'] += 1
            full_url = f"{base_url}{rel_url}"
            print(f"Processing: {title} ({full_url})")
            
            # Match movie
            matched_movie = find_movie_match(title, db_movies)
            
            if matched_movie:
                stats['matched'] += 1
                print(f"  Matched: '{title}' -> DB ID: {matched_movie.id} ({matched_movie.name})")

                # Process Showtimes
                try:
                    process_showtimes(session, full_url, matched_movie.id, stats)
                    session.commit() # Commit after each movie
                except Exception as e:
                    print(f"  Error processing showtimes for {title}: {e}")
            else:
                print(f"  No Match: '{title}'")
        
        # session.commit() # Done in loop

    print("\n=== Summary ===")
    print(f"Scraped {stats['scraped']} movies.")
    print(f"Matched {stats['matched']} movies.")
    print(f"Total Showtimes recorded: {stats['showtimes_recorded']}")

def process_showtimes(session, movie_url, movie_id, stats):
    # 1. Fetch Detail Page
    try:
        res = requests.get(movie_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
        # CRITICAL FIX: Force UTF-8 encoding for detail pages too
        res.encoding = 'utf-8' 
        soup = BeautifulSoup(res.text, 'html.parser')
    except Exception as e:
        print(f"  Failed to fetch detail: {e}")
        return

    # 2. Find Region Links in <select name="FORMS">
    select_form = soup.find('select', attrs={'name': 'FORMS'})
    if not select_form:
        print("  No showtime dropdown found.")
        return

    region_links = []
    for option in select_form.find_all('option'):
        val = option.get('value', '')
        text = option.get_text(strip=True)
        if '/showtime/' in val and text and '戲院查詢' not in text:
            full_link = f"http://www.atmovies.com.tw{val}" if val.startswith('/') else val
            region_links.append((text, full_link))
            
    if not region_links:
        print("  No region links found in dropdown.")
        return

    print(f"  Found {len(region_links)} regions.")

    # 3. Process each region
    total_showtimes_for_movie = 0
    today = date.today()
    
    for region_name, region_url in region_links:
        try:
            print(f"    Fetching {region_name} showtimes...")
            res_st = requests.get(region_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
            # CRITICAL FIX: Force UTF-8 encoding for showtime pages
            res_st.encoding = 'utf-8'
            soup_st = BeautifulSoup(res_st.text, 'html.parser')
            
            # Count times
            container = soup_st.find('div', id='filmShowtimeBlock')
            if not container:
                container = soup_st
            
            text_content = container.get_text("\n")
            # Regex for HH:MM with word boundaries (handling standard and fullwidth colon)
            time_pattern = re.compile(r'\b\d{1,2}[:：]\d{2}\b')
            
            all_times = time_pattern.findall(text_content)
            count = len(all_times)
            
            if count > 0:
                print(f"      Found {count} times.")
                # Save to DB
                record = DailyShowtime(
                    movie_id=movie_id,
                    date=today,
                    region=region_name,
                    showtime_count=count
                )
                session.add(record)
                total_showtimes_for_movie += count
            else:
                 print(f"      Found 0 times.")
                
        except Exception as e:
            print(f"    Error processing region {region_name}: {e}")

    if total_showtimes_for_movie > 0:
        stats['showtimes_recorded'] += total_showtimes_for_movie
        print(f"  Saved {total_showtimes_for_movie} showtimes total.")


if __name__ == "__main__":
    scrape_atmovies()
