import sqlite3
import os

db_path = 'boxoffice.db'

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        movie_count = c.execute("SELECT count(*) FROM movie").fetchone()[0]
        weekly_count = c.execute("SELECT count(*) FROM WeeklyBoxOffice").fetchone()[0]
        print(f"Movies Count: {movie_count}")
        print(f"Weekly Data Count: {weekly_count}")
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")
