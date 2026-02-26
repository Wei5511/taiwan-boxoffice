
import requests
from bs4 import BeautifulSoup
import re
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)

def debug_process_showtimes(movie_url):
    print(f"DEBUG: Processing {movie_url}")
    try:
        res = requests.get(movie_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
        res.encoding = res.apparent_encoding
        # Dump Detail HTML
        with open('debug_detail.html', 'w', encoding='utf-8') as f:
            f.write(res.text)
        print(f"  Dumped Detail HTML to debug_detail.html")
        soup = BeautifulSoup(res.text, 'html.parser')
    except Exception as e:
        print(f"  Failed to fetch detail: {e}")
        return

    # Direct test for Taipei (a02)
    target_url = "http://www.atmovies.com.tw/showtime/fmen31050594/a02/"
    print(f"  Fetching showtime page: {target_url}")
    
    try:
        res_st = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
        res_st.encoding = res_st.apparent_encoding
        print(f"  Final URL: {res_st.url}")
        print(f"  Status Code: {res_st.status_code}")
        
        # Dump HTML
        with open('debug_showtime_taipei.html', 'w', encoding='utf-8') as f:
            f.write(res_st.text)
        print("  Dumped HTML to debug_showtime_taipei.html")
        
        soup_st = BeautifulSoup(res_st.text, 'html.parser')
    except Exception as e:
        print(f"  Failed to fetch showtimes: {e}")
        return

    # Debug Parsing
    # Dump the structure of showtime block
    container = soup_st.find('div', id='filmShowtimeBlock')
    if container:
        print("  Found #filmShowtimeBlock")
        # Print first 500 chars of text
        text = container.get_text("\n")
        print(f"  Content Preview:\n{text[:500]}...")
    else:
        print("  #filmShowtimeBlock NOT found. Dumping main content preview...")
        # Search for ANY typical container
        main_content = soup_st.find('div', id='main') or soup_st.find('div', class_='content') or soup_st.find('body')
        if main_content:
            print(f"  Main/Body Content Preview:\n{main_content.get_text()[:500]}...")


    # Test logic
    regions = ["台北市", "新北市", "桃園", "新竹", "苗栗", "台中", "彰化", "南投", "雲林", "嘉義", "台南", "高雄", "屏東", "基隆", "宜蘭", "花蓮", "台東", "金門", "澎湖"]
    region_counts = {r: 0 for r in regions}
    current_region = "Unknown"
    
    text_content = container.get_text("\n") if container else soup_st.get_text("\n")
    lines = text_content.split('\n')
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check region
        found_region = False
        for r in regions:
            if r in line:
                print(f"  [DEBUG] Found region in line: '{line}' -> {r}")
                current_region = r
                found_region = True
                break
        
        # Count matches
        times = time_pattern.findall(line)
        if times:
            print(f"  [DEBUG] Found times in line ({current_region}): {times}")
            if current_region in region_counts:
                region_counts[current_region] += len(times)

    print("\n  Counts:")
    for r, c in region_counts.items():
        if c > 0:
            print(f"    {r}: {c}")

def main():
    # Find exact link for 關鍵公敵
    list_url = "http://www.atmovies.com.tw/movie/now/"
    res = requests.get(list_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    target_link = None
    for a in soup.find_all('a', href=True):
        if "關鍵公敵" in a.get_text():
            target_link = a['href']
            print(f"Found match: {a.get_text()} -> {target_link}")
            break
            
    if target_link:
        full_url = f"http://www.atmovies.com.tw{target_link}"
        debug_process_showtimes(full_url)
    else:
        print("Could not find '關鍵公敵' in the list.")

if __name__ == "__main__":
    main()
