import sqlite3

conn = sqlite3.connect('boxoffice.db')
cursor = conn.cursor()

# Get the movies that appear in the latest week but didn't appear in the previous week
cursor.execute("""
    SELECT m.name, m.release_date 
    FROM movie m
    JOIN weeklyboxoffice w ON m.id = w.movie_id
    WHERE w.report_date_end = '2026-02-22'
    AND m.id NOT IN (
        SELECT movie_id FROM weeklyboxoffice WHERE report_date_end = '2026-02-15'
    )
    ORDER BY m.release_date DESC
""")
new_this_week = cursor.fetchall()

print("Movies that appeared in 2026-02-22 week for the first time:")
for m in new_this_week:
    print(f"- {m[0]} (Released: {m[1]})")

conn.close()
