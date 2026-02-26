import sqlite3

conn = sqlite3.connect('movies.db')
cursor = conn.cursor()

# Check what the latest week is in weekly_boxoffice
cursor.execute("SELECT MAX(report_date_end) FROM weekly_boxoffice")
latest_week_end = cursor.fetchone()[0]
print(f"Latest week end in DB: {latest_week_end}")

cursor.execute("SELECT name, release_date FROM movies WHERE release_date >= '2026-02-15' AND release_date <= '2026-02-22'")
movies = cursor.fetchall()
print("New releases between 2026-02-15 and 2026-02-22:")
for m in movies:
    print(f"- {m[0]} ({m[1]})")
print(f"Total: {len(movies)}")

cursor.execute("SELECT name, release_date FROM movies ORDER BY release_date DESC LIMIT 10")
latest = cursor.fetchall()
print("\nTop 10 latest release dates in DB:")
for m in latest:
    print(f"- {m[0]} ({m[1]})")

conn.close()
