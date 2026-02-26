from playwright.sync_api import sync_playwright
import time

def inspect():
    url = "https://boxofficetw.tfai.org.tw/statistic"
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
        page.goto(url)
        time.sleep(10)
        
        # Look for the date range button
        # It usually contains specific date format or just find by the one we saw "2026-02-02到2026-02-08"
        # Using a regex locator might be safer as the date changes
        date_btn = page.locator('button').filter(has_text="到").first
        
        if date_btn.count() > 0:
            print(f"Found date button: {date_btn.inner_text()}")
            date_btn.click()
            time.sleep(2)
            
            # Now see what opened. Likely a list of options.
            # Check for list items or other buttons
            options = page.locator('ul li, .dropdown-menu li, div[role="option"]').all()
            print(f"Found {len(options)} potential options after click")
            
            for i, opt in enumerate(options[:20]):
                print(f"Option {i}: {opt.inner_text().strip()}")
                
        else:
            print("Could not find date button with '到'")
            
            # Check if there are select elements
            selects = page.locator('select').all()
            print(f"Found {len(selects)} select elements")
            for i, sel in enumerate(selects):
                opts = sel.locator('option').all()
                print(f"Select {i} has {len(opts)} options")
                if len(opts) > 0:
                    print(f"First option: {opts[0].inner_text()}")
                    print(f"Last option: {opts[-1].inner_text()}")

        browser.close()

if __name__ == "__main__":
    inspect()
