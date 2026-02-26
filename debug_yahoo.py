import requests
from bs4 import BeautifulSoup

url = "https://movies.yahoo.com.tw/movie_intheaters.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
with open('yahoo_debug.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"Saved to yahoo_debug.html. Size: {len(response.text)} bytes")

soup = BeautifulSoup(response.text, 'html.parser')
# Try to find a known movie
target_movie = "關鍵公敵"
found = soup.find_all(string=lambda text: target_movie in text if text else False)

print(f"Searching for '{target_movie}':")
for element in found:
    print(f"Found in tag: {element.parent.name}")
    print(f"Parent class: {element.parent.get('class')}")
    # Print a bit of the surrounding HTML
    print(f"Context: {element.parent.parent}")
    print("-" * 20)
