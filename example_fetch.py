"""
Example: Fetch specific week's data
Demonstrates how to fetch data for a specific date
"""

from scrape_boxoffice import scrape_boxoffice_data
from datetime import datetime

# Fetch data for the week of January 1, 2024
# This will fetch the Monday-Sunday week containing this date
target_date = datetime(2024, 1, 1)

print("Fetching Taiwan Box Office data for a specific week...")
print(f"Target date: {target_date.strftime('%Y-%m-%d')}\n")

df = scrape_boxoffice_data(target_date)

if df is not None:
    print("\n" + "="*80)
    print("SUCCESS! Data retrieved and parsed.")
    print("="*80)
