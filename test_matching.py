from scrape_atmovies import find_movie_match, normalize_name
from models import Movie

# Mock DB movies
mock_db = [
    Movie(name="陽光女子合唱團", id=1),
    Movie(name="功夫熊貓 4", id=2),
    Movie(name="周處除三害", id=3),
]

# Test cases
test_cases = [
    "陽光女子合唱團",
    "陽光女子合唱團 (2024)",
    "陽光女子合唱團 (數位版)",
    "功夫 (2026)",
    "周處除三害 (2023)",
]

print("Testing Matching Logic...")
for case in test_cases:
    print(f"\nTesting: '{case}'")
    match = find_movie_match(case, mock_db)
    if match:
        print(f"✅ Matched: '{match.name}'")
    else:
        print(f"❌ No Match")

print("\nNormalization Check:")
print(f"'陽光女子合唱團 (2024)' -> '{normalize_name('陽光女子合唱團 (2024)')}'")
