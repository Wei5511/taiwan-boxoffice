import os
import urllib.parse
from sqlmodel import SQLModel, create_engine, Session
import psycopg2

# === THE ABSOLUTE FINAL NUCLEAR FIX ===
# Bypass SQLAlchemy URL string parsing completely using `creator` function.

# Force PostgreSQL if DATABASE_URL is present.
# No silent fallback to SQLite in production if the env var exists but connection fails.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    print("[database.py] 🚀 DATABASE_URL detected. Forcing PostgreSQL (bypassing URL parsing).")
    def get_conn():
        return psycopg2.connect(
            host="aws-0-ap-northeast-1.pooler.supabase.com",
            port=5432,
            user="postgres.ufiwrwbfbxyqamkikpia",
            password="Wei03230501!",  # Raw password, no URL parsing
            database="postgres",
            sslmode="require"
        )
    engine = create_engine("postgresql+psycopg2://", creator=get_conn, echo=False)
else:
    print("[database.py] ⚠️ DATABASE_URL not found. Falling back to SQLite.")
    sqlite_file_name = "boxoffice.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
