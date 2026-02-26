from playwright.sync_api import sync_playwright
import json
import time

def inspect():
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
        
        # Capture network requests
        print("Starting network capture...")
        
        def handle_response(response):
            if "json" in response.headers.get("content-type", "") or "api" in response.url:
                try:
                    print(f"Response: {response.url} ({response.status})")
                    # data = response.json()
                    # print(json.dumps(data, ensure_ascii=False)[:200] + "...")
                except:
                    pass

        page.on("response", handle_response)
        
        print("Navigating to https://boxofficetw.tfai.org.tw/statistic")
        page.goto("https://boxofficetw.tfai.org.tw/statistic")
        
        time.sleep(5)
        
        # Try to click the date button again to trigger requests
        print("Attempting to interact with date button...")
        date_btn = page.locator('button').filter(has_text="到").first
        if date_btn.count() > 0:
            date_btn.click()
            time.sleep(2)
        
        # Try to click "Query" button
        print("Attempting to click Query button...")
        query_btn = page.locator('button:has-text("查詢")').first
        if query_btn.count() > 0:
            query_btn.click()
            time.sleep(5)
            
        browser.close()

if __name__ == "__main__":
    inspect()
