import os
import urllib.parse
from sqlmodel import SQLModel, create_engine, Session

# === PERMANENT FIX: Hardcode-safe URL assembly ===
# Force-encode the password and construct the URL manually
# to prevent special characters (like '!') from breaking URL parsing.

DB_USER = os.getenv("DB_USER", "postgres.ufiwrwbfbxyqamkikpia")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Wei03230501!")
DB_HOST = os.getenv("DB_HOST", "aws-0-ap-northeast-1.pooler.supabase.com")
DB_PORT = os.getenv("DB_PORT", "6543")
DB_NAME = os.getenv("DB_NAME", "postgres")

IS_PRODUCTION = bool(os.getenv("DATABASE_URL") or os.getenv("RENDER"))

if IS_PRODUCTION:
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = (
        f"postgresql://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?sslmode=require"
    )
    print(f"[database.py] Using PostgreSQL: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    engine = create_engine(DATABASE_URL, echo=False)
else:
    sqlite_file_name = "boxoffice.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    print(f"[database.py] Using SQLite: {sqlite_url}")
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
