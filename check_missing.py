import sqlite3

conn = sqlite3.connect('boxoffice.db')
cursor = conn.cursor()

# Get the movies that appear in the latest week but have NO release date
cursor.execute("""
    SELECT m.name 
    FROM movie m
    JOIN weeklyboxoffice w ON m.id = w.movie_id
    WHERE w.report_date_end = '2026-02-22'
    AND (m.release_date IS NULL OR m.release_date = '')
""")
missing = cursor.fetchall()
print(f"Movies missing release dates in 2026-02-22: {len(missing)}")
if missing:
    for m in missing[:10]:
        print(f" - {m[0]}")

"""
Let's also see what movies have release_date between 2026-02-15 and 2026-02-22. Wait, we already checked, it's 0.
How about between 2026-02-09 and 2026-02-15? We had maybe 15.
"""

conn.close()
