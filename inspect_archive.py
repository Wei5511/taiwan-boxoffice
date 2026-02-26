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
        
        # Test 1: Click "2016年至今票房"
        print("Test 1: Clicking '2016年至今票房'")
        page.goto("https://boxofficetw.tfai.org.tw/statistic")
        time.sleep(5)
        
        archive_link = page.locator('a, button').filter(has_text="2016年至今票房").first
        if archive_link.count() > 0:
            print("Found archive link, clicking...")
            archive_link.click()
            time.sleep(5)
            print(f"New URL: {page.url}")
            print(f"New Title: {page.title()}")
            
            # Check for year links
            years = page.locator('text=2024').all()
            print(f"Found {len(years)} elements with '2024' on new page")
        else:
            print("Could not find '2016年至今票房' link")
            
        # Test 2: URL parameter
        print("\nTest 2: URL parameter 'year=2024'")
        page.goto("https://boxofficetw.tfai.org.tw/statistic?year=2024")
        time.sleep(5)
        print(f"URL: {page.url}")
        # Check if we see 2024 data
        if "2024" in page.content():
            print("Page content contains '2024'")
        else:
            print("Page content does not contain '2024'")

        browser.close()

if __name__ == "__main__":
    inspect()
