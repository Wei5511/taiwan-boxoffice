import sqlite3

conn = sqlite3.connect('boxoffice.db')
cursor = conn.cursor()

cursor.execute("SELECT MAX(report_date_end) FROM weeklyboxoffice")
latest = cursor.fetchone()[0]
print(f"Latest week: {latest}")

main_countries = ['台灣', '美國', '日本', '韓國', '香港', '泰國', '越南', '馬來西亞', '新加坡', '印尼', '菲律賓', '東南亞']
placeholders = ', '.join(['?'] * len(main_countries))

query = f"""
    SELECT COUNT(*) 
    FROM movie m 
    JOIN weeklyboxoffice w ON m.id = w.movie_id 
    WHERE w.report_date_end = '{latest}'
    AND m.country NOT IN ({placeholders})
"""
cursor.execute(query, main_countries)
count = cursor.fetchone()[0]
print(f"Movies in '其他' for latest week: {count}")

query_all = f"""
    SELECT COUNT(*) 
    FROM movie m 
    JOIN weeklyboxoffice w ON m.id = w.movie_id 
    WHERE w.report_date_end = '{latest}'
"""
cursor.execute(query_all)
count_all = cursor.fetchone()[0]
print(f"Total movies for latest week: {count_all}")

conn.close()
