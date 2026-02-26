
import requests
from bs4 import BeautifulSoup
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)

url = "http://www.atmovies.com.tw/movie/now/"

try:
    print(f"Fetching {url}...")
    # Use verify=False to bypass SSL errors
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Apparent Encoding: {response.apparent_encoding}")
    
    response.encoding = response.apparent_encoding
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n--- Page Title ---")
    print(soup.title.string if soup.title else "No Title")
    
    print("\n--- Movie Links (First 10) ---")
    links = soup.find_all('a', href=True)
    count = 0
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if '/movie/' in href and text:
            print(f"{text} -> {href}")
            count += 1
            if count >= 10:
                break
                
except Exception as e:
    print(f"Error: {e}")
