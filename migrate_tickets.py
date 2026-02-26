import sqlite3
import os

db_path = "boxoffice.db"

def migrate():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Add column if it doesn't exist
        print("Adding cumulative_tickets column to weeklyboxoffice...")
        try:
            cursor.execute("ALTER TABLE weeklyboxoffice ADD COLUMN cumulative_tickets INTEGER")
        except sqlite3.OperationalError:
            print("Column cumulative_tickets already exists.")

        # 2. Backfill cumulative_tickets
        print("Backfilling cumulative_tickets data...")
        # Get all movies
        movies = cursor.execute("SELECT id FROM movie").fetchall()
        
        for movie in movies:
            movie_id = movie[0]
            # Get all records for this movie ordered by date
            records = cursor.execute("""
                SELECT id, weekly_tickets 
                FROM weeklyboxoffice 
                WHERE movie_id = ? 
                ORDER BY report_date_start ASC
            """, (movie_id,)).fetchall()
            
            cumulative = 0
            for record in records:
                record_id = record[0]
                weekly = record[1] or 0
                cumulative += weekly
                cursor.execute("""
                    UPDATE weeklyboxoffice 
                    SET cumulative_tickets = ? 
                    WHERE id = ?
                """, (cumulative, record_id))
        
        conn.commit()
        print("✓ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
