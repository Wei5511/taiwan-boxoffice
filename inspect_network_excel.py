from playwright.sync_api import sync_playwright
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
        
        print("Starting network capture...")
        
        def handle_request(request):
            if "export" in request.url or "xlsx" in request.url or "Excel" in request.url:
                print(f"Request: {request.url}")
        
        page.on("request", handle_request)
        
        print("Navigating to https://boxofficetw.tfai.org.tw/statistic")
        page.goto("https://boxofficetw.tfai.org.tw/statistic")
        
        time.sleep(5)
        
        # Click Excel button
        # Based on previous inspection, there is an Item 12: Excel
        # It might be a button with text "Excel"
        print("Attempting to click Excel button...")
        excel_btn = page.locator('button:has-text("Excel"), a:has-text("Excel")').first
        
        if excel_btn.count() > 0:
            print("Found Excel button, clicking...")
            try:
                with page.expect_download(timeout=10000) as download_info:
                    excel_btn.click()
                download = download_info.value
                print(f"Download started: {download.url}")
                print(f"Suggested filename: {download.suggested_filename}")
            except Exception as e:
                print(f"Error clicking or downloading: {e}")
        else:
            print("Excel button not found")

        browser.close()

if __name__ == "__main__":
    inspect()
