"""
Database Connection Diagnostic Script for Render/Supabase
=========================================================
This script tests multiple PostgreSQL connection variations
to identify which one works with the current DATABASE_URL.

Run with: python test_db.py
Results will appear in Render logs.
"""
import os
import sys
import traceback
from urllib.parse import urlparse, unquote

def diagnose():
    db_url = os.getenv("DATABASE_URL")
    
    print("=" * 60)
    print("DATABASE CONNECTION DIAGNOSTIC")
    print("=" * 60)
    
    if not db_url:
        print("[FATAL] DATABASE_URL is NOT set in environment variables.")
        print("        Set it in Render Dashboard > Environment > DATABASE_URL")
        return
    
    # --- Step 1: Parse the URL ---
    print("\n--- Step 1: URL Analysis ---")
    parsed = urlparse(db_url)
    
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    hostname = parsed.hostname or ""
    port = parsed.port or 5432
    dbname = (parsed.path or "").lstrip("/")
    
    print(f"  Scheme:   {parsed.scheme}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * min(len(password), 8)}{'...' if len(password) > 8 else ''} (len={len(password)})")
    print(f"  Hostname: {hostname}")
    print(f"  Port:     {port}")
    print(f"  Database: {dbname}")
    
    # Check for common issues
    if "!" in (parsed.password or ""):
        print("  [WARNING] Password contains '!' - check URL encoding (%21)")
    if "%" in (parsed.password or ""):
        print("  [INFO] Password contains URL-encoded characters")

    # Extract project ID from username (e.g., postgres.ufiwrwbfbxyqamkikpia)
    project_id = None
    if "." in username:
        project_id = username.split(".", 1)[1]
        print(f"  Project ID: {project_id}")
    else:
        print(f"  [INFO] No project ID in username (format: {username})")
    
    # --- Step 2: Try psycopg2 import ---
    print("\n--- Step 2: psycopg2 Check ---")
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        print(f"  psycopg2 version: {psycopg2.__version__}")
    except ImportError:
        print("  [FATAL] psycopg2 is NOT installed!")
        print("  Add 'psycopg2-binary' to requirements.txt")
        return
    
    # --- Step 3: Connection Tests ---
    print("\n--- Step 3: Connection Tests ---")
    
    # Build connection variations
    variations = {}
    
    # A: Use the raw DATABASE_URL as-is
    variations["A: Raw DATABASE_URL (as-is)"] = db_url
    
    # If we detected a project ID, try Supabase-specific variations
    if project_id:
        # B: Standard Pooler (port 6543)
        pooler_host = f"aws-0-us-east-1.pooler.supabase.com"
        variations[f"B: Pooler port 6543"] = (
            f"postgresql://postgres.{project_id}:{password}"
            f"@{pooler_host}:6543/{dbname}"
        )
        
        # C: Session Pooler (port 5432)
        variations[f"C: Pooler port 5432"] = (
            f"postgresql://postgres.{project_id}:{password}"
            f"@{pooler_host}:5432/{dbname}"
        )
        
        # D: Direct Connect
        direct_host = f"db.{project_id}.supabase.co"
        variations[f"D: Direct Connect (db.{project_id})"] = (
            f"postgresql://postgres:{password}"
            f"@{direct_host}:5432/{dbname}"
        )
    
    working_url = None
    
    for label, url in variations.items():
        # Sanitize for logging
        p = urlparse(url)
        safe_url = f"{p.scheme}://{p.username}:***@{p.hostname}:{p.port}{p.path}"
        print(f"\n  [{label}]")
        print(f"    URL: {safe_url}")
        
        try:
            conn = psycopg2.connect(url, connect_timeout=10, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM movie")
            result = cursor.fetchone()
            movie_count = result["cnt"] if result else 0
            cursor.close()
            conn.close()
            print(f"    ✅ SUCCESS! Connected. Movie count: {movie_count}")
            if not working_url:
                working_url = url
        except Exception as e:
            print(f"    ❌ FAILED: {e}")
    
    # --- Summary ---
    print("\n" + "=" * 60)
    if working_url:
        p = urlparse(working_url)
        safe = f"{p.scheme}://{p.username}:***@{p.hostname}:{p.port}{p.path}"
        print(f"RESULT: Working connection found!")
        print(f"USE THIS URL FORMAT: {safe}")
    else:
        print("RESULT: ALL connections failed!")
        print("Check your DATABASE_URL, password, and Supabase project status.")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()
