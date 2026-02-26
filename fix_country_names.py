#!/usr/bin/env python3
"""
Database Fix Script: Update country names from 中華民國 to 台灣
This fixes the search issue where searching for "台灣" returns no results.
"""

from sqlmodel import Session, create_engine, select
from models import Movie

# Database connection
DATABASE_URL = "sqlite:///./boxoffice.db"
engine = create_engine(DATABASE_URL, echo=True)

def fix_country_names():
    """Update all movies with country='中華民國' to country='台灣'"""
    
    with Session(engine) as session:
        # Find all movies with 中華民國
        statement = select(Movie).where(Movie.country == "中華民國")
        movies_to_update = session.exec(statement).all()
        
        count = len(movies_to_update)
        
        if count == 0:
            print("✅ No movies found with country='中華民國'. Database is already clean!")
            return
        
        print(f"🔍 Found {count} movies with country='中華民國'")
        print(f"📝 Updating to '台灣'...")
        
        # Update each movie
        for movie in movies_to_update:
            movie.country = "台灣"
        
        # Commit changes
        session.commit()
        
        print(f"✅ Successfully updated {count} movies!")
        print(f"   Country changed: 中華民國 → 台灣")

if __name__ == "__main__":
    print("=" * 60)
    print("Database Country Name Fix Script")
    print("=" * 60)
    fix_country_names()
    print("=" * 60)
    print("✨ Script complete!")
