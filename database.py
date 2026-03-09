import os
from urllib.parse import quote_plus
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # === NUCLEAR FIX: Manually construct the URL ===
    # The raw DATABASE_URL from Render/Supabase can have special characters
    # (like '!' in the password) that break URL parsing.
    # We manually construct it with proper encoding.
    
    DB_USER = os.getenv("DB_USER", "postgres.ufiwrwbfbxyqamkikpia")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Wei03230501!")
    DB_HOST = os.getenv("DB_HOST", "aws-0-ap-northeast-1.pooler.supabase.com")
    DB_PORT = os.getenv("DB_PORT", "6543")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    
    # quote_plus ensures '!' and other special chars are properly escaped
    encoded_password = quote_plus(DB_PASSWORD)
    
    # SQLAlchemy requires 'postgresql://' scheme
    CONSTRUCTED_URL = (
        f"postgresql://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    print(f"[database.py] Using PostgreSQL engine")
    print(f"[database.py]   Host: {DB_HOST}:{DB_PORT}")
    print(f"[database.py]   User: {DB_USER}")
    print(f"[database.py]   DB:   {DB_NAME}")
    
    engine = create_engine(
        CONSTRUCTED_URL,
        echo=False,
        connect_args={"sslmode": "require"}
    )
else:
    sqlite_file_name = "boxoffice.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    print(f"[database.py] Using SQLite engine: {sqlite_url}")
    engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
