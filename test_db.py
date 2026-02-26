import sqlite3

conn = sqlite3.connect('boxoffice.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

if ('movie',) in tables:
    cursor.execute("PRAGMA table_info(movie)")
    print("Movies schema:", cursor.fetchall())
    cursor.execute("SELECT name, release_date FROM movie WHERE release_date >= '2026-02-15' AND release_date <= '2026-02-22'")
    movies = cursor.fetchall()
    print("New releases between 2026-02-15 and 2026-02-22:")
    for m in movies:
        print(f"- {m[0]} ({m[1]})")
    print(f"Total: {len(movies)}")

    cursor.execute("SELECT name, release_date FROM movie ORDER BY release_date DESC LIMIT 5")
    print("Recent movies:", cursor.fetchall())

if ('weeklyboxoffice',) in tables:
    cursor.execute("SELECT MAX(report_date_end) FROM weeklyboxoffice")
    print("Latest week end:", cursor.fetchone()[0])

conn.close()
