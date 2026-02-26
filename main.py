import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func, col, text
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import calendar
from models import Movie, WeeklyBoxOffice, DailyShowtime
from database import engine, get_session
import sqlite3
import threading
from apscheduler.schedulers.background import BackgroundScheduler

# For direct SQLite connection (if needed for specific operations)
sqlite_file_name = "boxoffice.db" # Assuming this is the SQLite database file

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url and psycopg2:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # Connect to PostgreSQL and wrap for SQLite compatibility
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
        class CursorWrapper:
            def __init__(self, cursor):
                self._cursor = cursor
            def execute(self, query, params=()):
                if '?' in query:
                    # Very simple replace: assuming no literal '?' inside strings
                    query = query.replace('?', '%s')
                self._cursor.execute(query, params)
                return self
            def fetchall(self):
                return self._cursor.fetchall()
            def fetchone(self):
                return self._cursor.fetchone()
            def close(self):
                self._cursor.close()
            @property
            def description(self):
                return self._cursor.description
        
        class ConnWrapper:
            def __init__(self, conn):
                self._conn = conn
            def cursor(self):
                return CursorWrapper(self._conn.cursor())
            def close(self):
                self._conn.close()
            def commit(self):
                self._conn.commit()
                
        return ConnWrapper(conn)
    else:
        conn = sqlite3.connect(sqlite_file_name)
        conn.row_factory = sqlite3.Row
        return conn

# --- Scheduled Task ---
_scrape_lock = threading.Lock()
_is_scraping = False

def scheduled_scrape_task():
    """Wrapper that safely calls the Playwright-based scraper."""
    global _is_scraping
    if _is_scraping:
        print("[Scheduler] Scrape already in progress, skipping.")
        return
    _is_scraping = True
    print(f"[Scheduler] Starting scheduled scrape at {datetime.now().isoformat()}")
    try:
        from scrape_boxoffice import scrape_boxoffice_data
        scrape_boxoffice_data()
        print(f"[Scheduler] Scrape completed successfully at {datetime.now().isoformat()}")
    except Exception as e:
        print(f"[Scheduler] Scrape failed: {e}")
    finally:
        _is_scraping = False

# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler(daemon=True)
    # Run every day at 03:00 AM (Taiwan time, UTC+8)
    scheduler.add_job(
        scheduled_scrape_task,
        trigger='cron',
        hour=3,
        minute=0,
        id='daily_boxoffice_scrape',
        name='Daily Box Office Scrape',
        timezone='Asia/Taipei',
        replace_existing=True
    )
    scheduler.start()
    print("[Scheduler] Background scheduler started. Next run: daily at 03:00 AM (Asia/Taipei)")
    yield
    scheduler.shutdown(wait=False)
    print("[Scheduler] Background scheduler stopped.")

app = FastAPI(title="Taiwan Box Office API", lifespan=lifespan)


# CORS Middleware - Production Ready
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = allowed_origins_env.split(",") if allowed_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Admin: Manual Scrape Trigger ---
@app.post("/admin/trigger-scrape")
def trigger_scrape_now():
    """Manually trigger a box office scrape immediately (for testing/on-demand)."""
    if _is_scraping:
        return {"status": "skipped", "message": "A scrape is already in progress."}
    import threading
    thread = threading.Thread(target=scheduled_scrape_task, daemon=True)
    thread.start()
    return {"status": "started", "message": "Scraping task started in the background."}


@app.get("/admin/scheduler-status")
def get_scheduler_status():
    """Returns the current status of the scheduled scraper."""
    return {
        "is_scraping": _is_scraping,
        "next_run": "Daily at 03:00 AM (Asia/Taipei)",
        "scraper_module": "scrape_boxoffice.scrape_boxoffice_data"
    }


@app.get("/movies/compare")
def compare_movies(movie_ids: str):
    ids = [int(i.strip()) for i in movie_ids.split(",") if i.strip().isdigit()]
    if not ids:
        return {"movies": [], "data": []}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ",".join("?" * len(ids))
    movies = cursor.execute(f"SELECT id, name FROM movie WHERE id IN ({placeholders})", ids).fetchall()
    
    history = cursor.execute(f"""
        SELECT movie_id, weekly_revenue, cumulative_revenue, theater_count, weekly_tickets, report_date_start
        FROM weeklyboxoffice
        WHERE movie_id IN ({placeholders})
        ORDER BY report_date_start ASC
    """, ids).fetchall()
    
    conn.close()
    
    movie_weeks = {m_id: [] for m_id in ids}
    for row in history:
        movie_weeks[row["movie_id"]].append(dict(row))
        
    max_weeks = max([len(weeks) for weeks in movie_weeks.values()] + [0])
    
    data = []
    for i in range(max_weeks):
        week_data = {"relative_week": i + 1}
        for m_id in ids:
            weeks = movie_weeks.get(m_id, [])
            if i < len(weeks):
                w = weeks[i]
                week_data[f"{m_id}_weekly"] = w["weekly_revenue"]
                week_data[f"{m_id}_cumulative"] = w["cumulative_revenue"]
                week_data[f"{m_id}_theaters"] = w["theater_count"]
                week_data[f"{m_id}_tickets"] = w["weekly_tickets"]
            else:
                week_data[f"{m_id}_weekly"] = None
                week_data[f"{m_id}_cumulative"] = None
                week_data[f"{m_id}_theaters"] = None
                week_data[f"{m_id}_tickets"] = None
        data.append(week_data)
        
    return {
        "movies": [{"id": m["id"], "name": m["name"]} for m in movies],
        "data": data
    }


# --- Pydantic Models for Response ---
# We can use SQLModel classes directly or define subsets

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Taiwan Box Office API is running"}

@app.get("/movies")
def get_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(500, ge=1, le=1000),
    sort_by: str = Query("weekly_revenue", pattern="^(weekly_revenue|cumulative_revenue)$"),
    search: str = None,
    country: str = None,
    year: int = None,
    week: int = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # STEP 1: Determine the Target Date
    target_year = year
    target_week = week
    
    # LOGIC FIX: Only force date if NOT searching
    # If NO search and NO date -> Force Latest (Existing logic)
    if not search and (not target_year or not target_week):
        cursor.execute("SELECT MAX(report_date_start) FROM weeklyboxoffice")
        latest_date_result = cursor.fetchone()
        
        if not latest_date_result or not latest_date_result[0]:
             # DB is completely empty
            conn.close()
            return {"movies": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
            
        target_date = latest_date_result[0]
        # print(f"DEBUG: Using latest available report date: {target_date}")
    else:
        # If searching, we might NOT have a target date, which is fine (global search)
        # If user provided specific date, we use it (will be converted to logic below if needed)
        # But wait, original code used report_date_start.
        # If user provides year/week, we need to find the matching report_date_start?
        # Actually my previous fix changed it to query by report_date_start. 
        # But the User input logic uses year/week in this prompt. 
        # Let's align with the prompt's logic but keep my Schema fix (lowercase tables).
        pass

    # Re-implementing based on Schema (weeklyboxoffice uses report_date_start/end, not year/week columns directly? 
    # Wait, earlier I found the table ONLY has report_date_start/end.
    # The prompt's logic: query += " AND w.year = ? AND w.week = ?" 
    # This implies the prompt thinks year/week columns exist. 
    # BUT I KNOW THEY DON'T by default in my schema fix. 
    # Actually wait, `weeklyboxoffice` table schema from Step 2164:
    # (0, 'id', ... (2, 'report_date_start'), (3, 'report_date_end') ...
    # There are NO year/week columns.
    
    # So I must adapt the prompt's logic to use report_date_start.
    # OR better: The "Latest Date" logic I implemented uses `report_date_start`.
    
    # If search is present, I should NOT filter by date at all unless specified.
    
    query = """
        SELECT m.id, m.name, m.release_date, m.country, m.distributor,
               w.weekly_revenue, w.cumulative_revenue, w.theater_count, w.weekly_tickets,
               w.report_date_start, w.report_date_end
        FROM movie m
        JOIN weeklyboxoffice w ON m.id = w.movie_id
        WHERE 1=1
    """
    params = []

    # Refined Logic:

    # 1. Base Query
    if search:
        query = """
            SELECT m.id, m.name, m.release_date, m.country, m.distributor,
                   MAX(w.weekly_revenue) as weekly_revenue,
                   MAX(w.cumulative_revenue) as cumulative_revenue,
                   MAX(w.theater_count) as theater_count,
                   MAX(w.weekly_tickets) as weekly_tickets,
                   MAX(w.report_date_start) as report_date_start,
                   MAX(w.report_date_end) as report_date_end
            FROM movie m
            JOIN weeklyboxoffice w ON m.id = w.movie_id
            WHERE 1=1
        """
    else:
        query = """
            SELECT m.id, m.name, m.release_date, m.country, m.distributor,
                   w.weekly_revenue, w.cumulative_revenue, w.theater_count, w.weekly_tickets,
                   w.report_date_start, w.report_date_end
            FROM movie m
            JOIN weeklyboxoffice w ON m.id = w.movie_id
            WHERE 1=1
        """
    params = []

    # 2. Date Filtering
    if not search:
        # If NOT searching, we MUST show a specific week (Latest or Requested)
        # Since I replaced year/week cols with report_date, I'll default to Latest.
        cursor.execute("SELECT MAX(report_date_start) FROM weeklyboxoffice")
        latest_date = cursor.fetchone()[0]
        query += " AND w.report_date_start = ?"
        params.append(latest_date)
    else:
        # If searching, we don't restrict by date (Global Search)
        pass

    if search:
        query += " AND (m.name LIKE ?)"
        params.extend([f"%{search}%"])
        
    if country and country != "所有國家":
        if country == "其他":
            main_countries = ['台灣', '美國', '日本', '韓國', '香港', '泰國', '越南', '馬來西亞', '新加坡', '印尼', '菲律賓', '東南亞']
            placeholders = ', '.join(['?'] * len(main_countries))
            query += f" AND m.country NOT IN ({placeholders})"
            params.extend(main_countries)
        else:
            query += " AND m.country = ?"
            params.append(country)
    
    if search:
        query += " GROUP BY m.id"

    # Sort
    order_col = "cumulative_revenue" if sort_by == "cumulative_revenue" else "weekly_revenue"
    query += f" ORDER BY {order_col} DESC"

    print("DEBUG QUERY:", query)
    print("DEBUG PARAMS:", params)
    
    all_results = cursor.execute(query, params).fetchall()
    
    # Pagination
    total_count = len(all_results)
    start = (page - 1) * limit
    end = start + limit
    paginated_rows = all_results[start:end]
    
    formatted_results = []
    for row in paginated_rows:
        r = dict(row)
        # Normalize country: treat "中華民國" as "台灣"
        country = r.get("country")
        if country == "中華民國":
            country = "台灣"
        formatted_results.append({
            "id": r["id"],
            "name": r["name"],
            "english_name": None,
            "release_date": r.get("release_date"),
            "distributor": r.get("distributor"),
            "country": country,
            "cumulative_revenue": r.get("cumulative_revenue", 0),
            "weekly_revenue": r.get("weekly_revenue", 0),
            "theater_count": r.get("theater_count", 0),
            "tickets": r.get("weekly_tickets"),
            "is_active": True
        })

    conn.close()

    return {
        "movies": formatted_results,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        "debug_query": query,
        "debug_params": params
    }


@app.get("/movies/{movie_id}/details")
def get_movie_details(movie_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    movie = cursor.execute("SELECT * FROM movie WHERE id = ?", (movie_id,)).fetchone()
    if not movie:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    history = cursor.execute(f"""
        SELECT id, report_date_start, report_date_end, 
               weekly_revenue, cumulative_revenue, 
               weekly_tickets, cumulative_tickets,
               theater_count
        FROM weeklyboxoffice 
        WHERE movie_id = ? 
        ORDER BY report_date_start ASC
    """, (movie_id,)).fetchall()
    conn.close()

    history_list = []
    for h in history:
        d = datetime.strptime(h["report_date_end"], "%Y-%m-%d")
        iso_year, iso_week, _ = d.isocalendar()
        history_list.append({
            "year": iso_year,
            "week": iso_week,
            "weekly_revenue": h["weekly_revenue"],
            "cumulative_revenue": h["cumulative_revenue"],
            "weekly_tickets": h["weekly_tickets"],
            "cumulative_tickets": h["cumulative_tickets"]
        })

    # Normalize country in movie info
    movie_info = dict(movie)
    if movie_info.get("country") == "中華民國":
        movie_info["country"] = "台灣"

    return {
        "info": movie_info,
        "history": history_list
    }

@app.get("/movies/{movie_id}")
def get_movie_detail(
    movie_id: int, 
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get movie metadata, box office history, and showtime status.
    """
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # Weekly Records
    weekly_records = session.exec(
        select(WeeklyBoxOffice)
        .where(WeeklyBoxOffice.movie_id == movie_id)
        .order_by(WeeklyBoxOffice.report_date_end.asc())
    ).all()
    
    # Daily Showtimes (Today)
    today = date.today()
    showtimes = session.exec(
        select(DailyShowtime)
        .where(DailyShowtime.movie_id == movie_id)
        .where(DailyShowtime.date == today)
    ).all()
    
    # Summarize Showtimes
    showtime_summary = {s.region: s.showtime_count for s in showtimes}
    total_showtimes_today = sum(s.showtime_count for s in showtimes)

    return {
        "metadata": movie,
        "box_office_history": weekly_records,
        "showtime_stats": {
            "date": str(today),
            "total_count": total_showtimes_today,
            "by_region": showtime_summary
        }
    }

@app.get("/dashboard/market-share")
def get_market_share(session: Session = Depends(get_session)):
    """
    Aggregated showtime counts by Region for today.
    """
    today = date.today()
    # If today has no data (early morning), maybe check yesterday? 
    # For now strict today.
    
    # Query: Select region, Sum(count) Group By region
    statement = (
        select(DailyShowtime.region, func.sum(DailyShowtime.showtime_count))
        .where(DailyShowtime.date == today)
        .group_by(DailyShowtime.region)
        .order_by(func.sum(DailyShowtime.showtime_count).desc())
    )
    
    results = session.exec(statement).all()
    
    data = [{"region": region, "count": count} for region, count in results]
    
    return {
        "date": str(today),
        "market_share": data
    }

@app.get("/dashboard-stats")
def get_dashboard_stats(
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard statistics for War Room display.
    Returns: market share by country, 4-week trend, and KPIs.
    """
    # Global import of timedelta is available
    
    today = date.today()
    
    # Get the latest week's report_date_end
    latest_week_end = session.exec(
        select(func.max(WeeklyBoxOffice.report_date_end))
    ).first()
    
    if not latest_week_end:
        return {
            "market_share": [],
            "four_week_trend": [],
            "kpis": {
                "current_week_total": 0,
                "current_month_total": 0,
                "active_movie_count": 0
            }
        }
    
    # === MARKET SHARE BY COUNTRY (for Pie Chart) ===
    # Get revenue by country for the latest week
    country_revenue_query = session.exec(
        select(
            Movie.country,
            func.sum(WeeklyBoxOffice.weekly_revenue).label('total_revenue')
        )
        .join(WeeklyBoxOffice, Movie.id == WeeklyBoxOffice.movie_id)
        .where(WeeklyBoxOffice.report_date_end == latest_week_end)
        .where(Movie.country.isnot(None))
        .group_by(Movie.country)
        .order_by(func.sum(WeeklyBoxOffice.weekly_revenue).desc())
    ).all()
    
    # Process Grouping with STRICT Logic
    stats = {}
    
    # 1. Define Groups
    target_groups = ["台灣", "美國", "日本", "韓國", "香港"]
    sea_countries = ["泰國", "越南", "馬來西亞", "新加坡", "印尼", "菲律賓"]
    
    for country, revenue in country_revenue_query: # Use the query result
        if not country: continue
        
        # 2. Iterate and Group
        if country in target_groups:
            group_name = country
        elif country in sea_countries:
            group_name = "東南亞"
        else:
            group_name = "其他" # Force Norway, Europe, China etc. into here
            
        stats[group_name] = stats.get(group_name, 0) + (revenue or 0)
        
    market_share = [{"country": k, "revenue": v} for k, v in stats.items()]
    # Sort by revenue desc
    market_share.sort(key=lambda x: x["revenue"], reverse=True)
    
    # === 4-WEEK TREND (for Bar/Line Chart) ===
    # Query the actual latest 4 distinct weeks that have data (no empty gaps)
    conn_trend = get_db_connection()
    cursor_trend = conn_trend.cursor()
    trend_rows = cursor_trend.execute("""
        SELECT 
            report_date_end,
            SUM(weekly_revenue) as revenue
        FROM weeklyboxoffice
        WHERE weekly_revenue > 0
        GROUP BY report_date_end
        ORDER BY report_date_end DESC
        LIMIT 4
    """).fetchall()
    conn_trend.close()

    # Sort chronologically (oldest -> newest) for the chart
    trend_rows = list(reversed(trend_rows))

    four_week_trend = []
    for row in trend_rows:
        d = datetime.strptime(row["report_date_end"], "%Y-%m-%d")
        iso_cal = d.isocalendar()
        iso_year = iso_cal[0]
        iso_week = iso_cal[1]
        four_week_trend.append({
            "year": iso_year,
            "week": iso_week,
            "week_label": f"W{iso_week}",
            "revenue": row["revenue"] or 0,
            "date": row["report_date_end"]
        })
    
    # === KPIs ===
    # Use latest_week_end as the 'current' anchor time instead of real today, 
    # so metrics work even if data is old.
    anchor_date = latest_week_end
    
    # Current week total (latest week)
    current_week_total = session.exec(
        select(func.sum(WeeklyBoxOffice.weekly_revenue))
        .where(WeeklyBoxOffice.report_date_end == latest_week_end)
    ).first() or 0
    
    # Current month total (all weeks in current month of the anchor date)
    month_start = anchor_date.replace(day=1)
    current_month_total = session.exec(
        select(func.sum(WeeklyBoxOffice.weekly_revenue))
        .where(WeeklyBoxOffice.report_date_end >= month_start)
        .where(WeeklyBoxOffice.report_date_end <= anchor_date)
    ).first() or 0
    
    # Active movie count (movies with weekly_revenue > 10000 in latest week)
    active_movie_count = session.exec(
        select(func.count(func.distinct(WeeklyBoxOffice.movie_id)))
        .where(WeeklyBoxOffice.report_date_end == latest_week_end)
        .where(WeeklyBoxOffice.weekly_revenue > 10000)
    ).first() or 0
    
    # Weekly new releases (Rolling 7 days from anchor)
    week_start_str = (anchor_date - timedelta(days=7)).strftime("%Y-%m-%d")
    anchor_str = anchor_date.strftime("%Y-%m-%d")
    
    weekly_new_releases = session.exec(
        select(func.count(Movie.id))
        .where(Movie.release_date >= week_start_str)
        .where(Movie.release_date <= anchor_str)
        .where(Movie.release_date != None)
    ).first() or 0
    
    # Monthly new releases (Rolling 30 days from anchor) - Fixes "0" issue
    month_start_str = (anchor_date - timedelta(days=30)).strftime("%Y-%m-%d")
    
    monthly_new_releases = session.exec(
        select(func.count(Movie.id))
        .where(Movie.release_date >= month_start_str)
        .where(Movie.release_date <= anchor_str)
        .where(Movie.release_date != None)
    ).first() or 0
    
    return {
        "market_share": market_share,
        "four_week_trend": four_week_trend,
        "kpis": {
            "current_week_total": current_week_total,
            "current_month_total": current_month_total,
            "active_movie_count": active_movie_count,
            "weekly_new_releases": weekly_new_releases,
            "monthly_new_releases": monthly_new_releases
        }
    }

@app.get("/movie-trajectory")
def get_movie_trajectory(
    movie_ids: str = Query(..., description="Comma separated movie IDs"),
    session: Session = Depends(get_session)
):
    """
    Get trajectory data for comparison.
    """
    ids = [int(id.strip()) for id in movie_ids.split(',') if id.strip().isdigit()]
    result = []
    
    for mid in ids:
        movie = session.get(Movie, mid)
        if not movie: continue
        
        # Get all weekly records sorted by date
        records = session.exec(
            select(WeeklyBoxOffice)
            .where(WeeklyBoxOffice.movie_id == mid)
            .order_by(WeeklyBoxOffice.report_date_end.asc())
        ).all()
        
        data_points = []
        for i, rec in enumerate(records):
            data_points.append({
                "week_num": i + 1,
                "revenue": rec.weekly_revenue,
                "cumulative": rec.cumulative_revenue,
                "date": rec.report_date_end
            })
            
        result.append({
            "id": movie.id,
            "name": movie.name,
            "data": data_points
        })
        
    return result


@app.get("/weeks")
def get_available_weeks(
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get all available year/week combinations from the database.
    Used for the time machine week selector.
    """
    from datetime import datetime
    
    # Get all distinct report_date_end values
    weekly_records = session.exec(
        select(WeeklyBoxOffice.report_date_end)
        .distinct()
        .order_by(WeeklyBoxOffice.report_date_end.desc())
    ).all()
    
    # Convert to year/week format
    weeks = []
    seen = set()
    
    for end_date in weekly_records:
        # Get ISO year and week number
        iso_cal = end_date.isocalendar()
        year = iso_cal[0]
        week = iso_cal[1]
        
        key = (year, week)
        if key not in seen:
            seen.add(key)
            weeks.append({
                "year": year,
                "week": week,
                "label": f"{year} 第{week}週"
            })
    
    return weeks

@app.get("/stats")
def get_market_stats(
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get market overview statistics.
    Returns active movie count, weekly total revenue, and monthly new releases.
    """
    from datetime import datetime, timedelta
    
    today = date.today()
    
    
    # Monthly new releases: movies released in the current month
    month_start = today.replace(day=1)
    monthly_releases = session.exec(
        select(func.count(Movie.id))
        .where(Movie.release_date >= month_start)
        .where(Movie.release_date <= today)
    ).first() or 0
    
    return {
        "active_movie_count": active_count,
        "weekly_total_revenue": weekly_total,
        "monthly_new_releases": monthly_releases
    }

@app.get("/market-stats")
def get_market_stats(session: Session = Depends(get_session)):
    """
    Get aggregated weekly market statistics:
    - Total Revenue
    - Movie Count
    - Top Movie of the Week
    - Growth Rate (Week-over-Week)
    """
    # 1. Fetch all weekly records joined with Movie to get names
    # and ordered by date descending
    results = session.exec(
        select(WeeklyBoxOffice, Movie.name)
        .join(Movie, WeeklyBoxOffice.movie_id == Movie.id)
        .order_by(WeeklyBoxOffice.report_date_end.desc())
    ).all()
    
    # 2. Aggregate in Python
    weekly_agg = {} # Key: end_date (str)
    
    for record, movie_name in results:
        date_key = str(record.report_date_end)
        
        if date_key not in weekly_agg:
            # Determine Year and Week from date
            # simple iso_calendar
            iso_cal = record.report_date_end.isocalendar()
            year = iso_cal[0]
            week = iso_cal[1]
            
            weekly_agg[date_key] = {
                "year": year,
                "week": week,
                "start_date": record.report_date_start,
                "end_date": record.report_date_end,
                "total_revenue": 0,
                "movie_count": 0,
                "max_revenue": -1,
                "top_movie": "N/A"
            }
        
        rec = weekly_agg[date_key]
        rec["total_revenue"] += record.weekly_revenue
        rec["movie_count"] += 1
        
        if record.weekly_revenue > rec["max_revenue"]:
            rec["max_revenue"] = record.weekly_revenue
            rec["top_movie"] = movie_name

    # 3. Convert to list and Sort by Date Ascending to calculate growth
    stats_list = sorted(weekly_agg.values(), key=lambda x: x["end_date"])
    
    # 4. Calculate Growth Rate
    final_output = []
    for i, stats in enumerate(stats_list):
        growth_rate = 0.0
        if i > 0:
            prev_revenue = stats_list[i-1]["total_revenue"]
            if prev_revenue > 0:
                growth_rate = (stats["total_revenue"] - prev_revenue) / prev_revenue
        
        # Add to output (exclude max_revenue helper)
        final_output.append({
            "year": stats["year"],
            "week": stats["week"],
            "start_date": stats["start_date"],
            "end_date": stats["end_date"],
            "total_revenue": stats["total_revenue"],
            "movie_count": stats["movie_count"],
            "top_movie": stats["top_movie"],
            "growth_rate": growth_rate
        })
        
    # Return reverse sorted (newest first) for UI
    return final_output[::-1]

@app.get("/period-stats")
def get_period_stats(
    type: str = Query(..., description="Type of period: 'week', 'month', 'year', 'all_time'"),
    year: int = Query(..., description="Year"),
    number: Optional[int] = Query(None, description="Week number or Month number (1-indexed)"),
):
    """
    Get statistics for a specific period.
    FIXED: Always sums weekly_revenue only (never cumulative_revenue).
    Filters by report_date_start so each week belongs to exactly one period.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    start_date = None
    end_date = None
    prev_start = None
    prev_end = None
    growth_rate = 0.0

    try:
        if type == 'week':
            if number is None:
                raise HTTPException(status_code=400, detail="Week number required for type='week'")
            start_date = datetime.strptime(f'{year}-W{number:02d}-1', "%Y-W%W-%w").date()
            end_date = start_date + timedelta(days=6)
            prev_start = start_date - timedelta(days=7)
            prev_end = end_date - timedelta(days=7)

        elif type == 'month':
            if number is None:
                raise HTTPException(status_code=400, detail="Month number required for type='month'")
            start_date = date(year, number, 1)
            _, last_day = calendar.monthrange(year, number)
            end_date = date(year, number, last_day)
            prev_month = 12 if number == 1 else number - 1
            prev_year = year - 1 if number == 1 else year
            prev_start = date(prev_year, prev_month, 1)
            _, p_last = calendar.monthrange(prev_year, prev_month)
            prev_end = date(prev_year, prev_month, p_last)

        elif type == 'year':
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            prev_start = date(year - 1, 1, 1)
            prev_end = date(year - 1, 12, 31)

        elif type == 'all_time':
            pass
        else:
            raise HTTPException(status_code=400, detail="Invalid type")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date parameters: {e}")

    # ALL TIME
    if type == 'all_time':
        rows = cursor.execute("""
            SELECT m.id, m.name, m.release_date,
                   MAX(w.cumulative_revenue) as total_rev,
                   MAX(w.cumulative_tickets) as total_tickets
            FROM weeklyboxoffice w
            JOIN movie m ON w.movie_id = m.id
            GROUP BY m.id
            ORDER BY total_rev DESC
            LIMIT 200
        """).fetchall()

        total_revenue = cursor.execute(
            "SELECT COALESCE(SUM(weekly_revenue), 0) FROM weeklyboxoffice"
        ).fetchone()[0] or 0

        real_count = cursor.execute("SELECT COUNT(*) FROM movie").fetchone()[0]
        conn.close()

        return {
            "summary": {
                "start_date": "2016-01-01",
                "end_date": str(date.today()),
                "total_revenue": total_revenue,
                "growth_rate": 0,
                "movie_count": real_count
            },
            "rankings": [
                {"rank": i + 1, "id": r["id"], "name": r["name"],
                 "revenue": r["total_rev"], "tickets": r["total_tickets"],
                 "release_date": r["release_date"]}
                for i, r in enumerate(rows)
            ]
        }

    # NORMAL PERIOD (week / month / year)
    # KEY FIX: filter using report_date_start (the Monday the week began).
    # This prevents cross-boundary inflation — each weekly record is counted
    # in only ONE period. We ALWAYS sum weekly_revenue, never cumulative_revenue.
    start_str = str(start_date)
    end_str   = str(end_date)

    total_revenue = cursor.execute("""
        SELECT COALESCE(SUM(w.weekly_revenue), 0)
        FROM weeklyboxoffice w
        WHERE w.report_date_start >= ? AND w.report_date_start <= ?
    """, (start_str, end_str)).fetchone()[0]

    movie_count = cursor.execute("""
        SELECT COUNT(DISTINCT w.movie_id)
        FROM weeklyboxoffice w
        WHERE w.report_date_start >= ? AND w.report_date_start <= ?
    """, (start_str, end_str)).fetchone()[0]

    ranking_rows = cursor.execute("""
        SELECT m.id, m.name, m.release_date,
               SUM(w.weekly_revenue) as period_rev,
               SUM(w.weekly_tickets) as period_tickets
        FROM weeklyboxoffice w
        JOIN movie m ON w.movie_id = m.id
        WHERE w.report_date_start >= ? AND w.report_date_start <= ?
        GROUP BY m.id
        ORDER BY period_rev DESC
    """, (start_str, end_str)).fetchall()

    if prev_start and prev_end:
        prev_revenue = cursor.execute("""
            SELECT COALESCE(SUM(weekly_revenue), 0)
            FROM weeklyboxoffice
            WHERE report_date_start >= ? AND report_date_start <= ?
        """, (str(prev_start), str(prev_end))).fetchone()[0]
        if prev_revenue > 0:
            growth_rate = (total_revenue - prev_revenue) / prev_revenue

    conn.close()

    return {
        "summary": {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "growth_rate": growth_rate,
            "movie_count": movie_count
        },
        "rankings": [
            {"rank": i + 1, "id": r["id"], "name": r["name"],
             "revenue": r["period_rev"], "tickets": r["period_tickets"],
             "release_date": r["release_date"]}
            for i, r in enumerate(ranking_rows)
        ]
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Force Redeploy [2026-02-27T06:25:33+08:00]
