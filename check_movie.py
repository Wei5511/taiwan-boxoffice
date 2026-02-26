import sqlite3
import os

db_path = 'boxoffice.db'

print("--- Checking DB Truth ---")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Adapt to our actual schema which uses report_date_start/end instead of year/week columns
cursor.execute('''
SELECT w.report_date_start, w.report_date_end, w.weekly_revenue, w.cumulative_revenue
FROM weeklyboxoffice w
JOIN movie m ON w.movie_id = m.id
WHERE m.name LIKE '%陽光女子合唱團%'
ORDER BY w.report_date_end DESC
LIMIT 5
''')
rows = cursor.fetchall()
print("Recent records for 陽光女子合唱團 (Start, End, Weekly, Cumulative):")
for r in rows:
    print(f"Start: {r[0]}, End: {r[1]}, Weekly: {r[2]}, Cumul: {r[3]}")

# Also check how many movies are considered "其他" loosely vs exactly
cursor.execute("SELECT COUNT(*) FROM movie WHERE country = '其他'")
print(f"Movies with exact country='其他': {cursor.fetchone()[0]}")

main_countries = ['台灣', '美國', '日本', '韓國', '香港', '泰國', '越南', '馬來西亞', '新加坡', '印尼', '菲律賓', '東南亞']
placeholders = ','.join(['?'] * len(main_countries))
cursor.execute(f"SELECT COUNT(*) FROM movie WHERE country NOT IN ({placeholders})", main_countries)
print(f"Movies that should be classified as '其他': {cursor.fetchone()[0]}")

conn.close()
