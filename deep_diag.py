import sqlite3
import urllib.request
import json

print("=" * 60)
print("STEP 1: Database Direct Check")
print("=" * 60)

conn = sqlite3.connect("boxoffice.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get the latest date
cursor.execute("SELECT MAX(report_date_start) as latest FROM weeklyboxoffice")
latest = cursor.fetchone()["latest"]
print(f"Latest report_date_start in DB: {latest}")

# Sample rows from that date
cursor.execute("""
    SELECT m.name, w.weekly_revenue, w.cumulative_revenue
    FROM weeklyboxoffice w
    JOIN movie m ON w.movie_id = m.id
    WHERE w.report_date_start = ?
    ORDER BY w.weekly_revenue DESC
    LIMIT 5
""", (latest,))
rows = cursor.fetchall()
print(f"\nTop 5 movies for {latest}:")
for row in rows:
    print(f"  {dict(row)}")

# Check type of cumulative_revenue
cursor.execute("SELECT cumulative_revenue, typeof(cumulative_revenue) FROM weeklyboxoffice WHERE cumulative_revenue IS NOT NULL LIMIT 5")
types = cursor.fetchall()
print("\ncumulative_revenue types in DB:")
for r in types:
    print(f"  value={r[0]}, type={r[1]}")

conn.close()

print("\n" + "=" * 60)
print("STEP 2: Live API Check")
print("=" * 60)

try:
    url = "http://127.0.0.1:8000/movies?limit=3"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    movies = data.get("movies", [])
    print(f"API returned {len(movies)} movies")
    if movies:
        movie = movies[0]
        print(f"Keys in response: {list(movie.keys())}")
        print(f"First movie: {movie}")
except Exception as e:
    print(f"API Error: {e}")

print("\n" + "=" * 60)
print("STEP 3: API with sort_by=cumulative_revenue")
print("=" * 60)

try:
    url = "http://127.0.0.1:8000/movies?limit=3&sort_by=cumulative_revenue"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    movies = data.get("movies", [])
    print(f"API returned {len(movies)} movies")
    if movies:
        movie = movies[0]
        print(f"Keys: {list(movie.keys())}")
        print(f"cumulative_revenue value: {movie.get('cumulative_revenue')}")
        print(f"First movie: {movie}")
except Exception as e:
    print(f"API Error: {e}")
