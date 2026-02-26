"""
Debug script to list movie IDs in the database
"""
from sqlmodel import Session, select
from database import engine
from models import Movie

def debug_movie_ids():
    with Session(engine) as session:
        # Get first 10 movies
        statement = select(Movie).limit(10)
        movies = session.exec(statement).all()
        
        print("=" * 60)
        print("First 10 Movies in Database:")
        print("=" * 60)
        
        if not movies:
            print("No movies found in database!")
            return
            
        for movie in movies:
            print(f"ID: {movie.id:4d} | Name: {movie.name}")
            
        print("=" * 60)
        print(f"Total movies checked: {len(movies)}")
        
        # Also check total count
        all_movies = session.exec(select(Movie)).all()
        print(f"Total movies in DB: {len(all_movies)}")
        print("=" * 60)

if __name__ == "__main__":
    debug_movie_ids()
