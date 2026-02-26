import sqlite3
import os

def run_diagnostic():
    # Find the DB file
    db_path = 'boxoffice.db'
    if not os.path.exists(db_path) and os.path.exists('backend/boxoffice.db'):
        db_path = 'backend/boxoffice.db'
    
    print(f"--- Checking Database at: {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Check table schema
        cursor.execute("PRAGMA table_info(weeklyboxoffice)")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"Columns in WeeklyBoxOffice: {columns}")
        
        # 2. Check if ANY cumulative revenue exists
        cursor.execute('''
            SELECT m.name, w.weekly_revenue, w.cumulative_revenue 
            FROM weeklyboxoffice w 
            JOIN movie m ON w.movie_id = m.id 
            WHERE w.cumulative_revenue IS NOT NULL AND w.cumulative_revenue != '' AND w.cumulative_revenue != '0' 
            LIMIT 3
        ''')
        rows = cursor.fetchall()
        if rows:
            print("Sample Data with Cumulative Revenue:")
            for row in rows:
                print(dict(row))
        else:
            print("!!! CRITICAL WARNING: NO valid cumulative_revenue found in the entire database !!!")
            
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == '__main__':
    run_diagnostic()
