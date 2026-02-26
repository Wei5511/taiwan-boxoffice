from playwright.sync_api import sync_playwright
import json
import time

def fetch():
    url = "https://boxofficetw.tfai.org.tw/stat/qsl?mode=Week&start=2026-02-02&ascending=false&orderedColumn=ReleaseDate&page=0&size=5&region=all"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()
        
        # Navigate to main page first to get cookies
        page.goto("https://boxofficetw.tfai.org.tw/statistic")
        time.sleep(5)
        
        # Now go to API URL
        # Since it returns JSON, the browser will likely display it in the body.
        # We can just get page.content() or use text()
        
        response = page.goto(url)
        # response body
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            # Maybe it's wrapped in HTML pre tag?
            content = page.inner_text("body")
            print(content[:500])

        browser.close()

if __name__ == "__main__":
    fetch()
