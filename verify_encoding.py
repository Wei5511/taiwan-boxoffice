from sqlmodel import Session, create_engine, select
from models import DailyShowtime

engine = create_engine("sqlite:///boxoffice.db")
session = Session(engine)

print("Checking Region Names in DB...")
regions = session.exec(select(DailyShowtime.region).distinct()).all()

print(f"Found {len(regions)} unique regions:")
clean_count = 0
dirty_count = 0

for r in regions:
    # simple heuristic: if it contains 'å', it's likely mojibake
    if 'å' in r or 'æ' in r or 'ç' in r:
         print(f"❌ MOJIBAKE: {r}")
         dirty_count += 1
    else:
         print(f"✅ CLEAN: {r}")
         clean_count += 1

print(f"\nSummary: {clean_count} clean, {dirty_count} dirty.")
if dirty_count == 0 and "金門" in regions:
    print("✨ VERIFICATION SUCCESS: All regions clean and '金門' found.")
elif dirty_count > 0:
    print("🔥 VERIFICATION FAILED: Mojibake still present.")
else:
    print("⚠️ VERIFICATION WARNING: No Mojibake, but '金門' not found (scraper might not have finished).")
