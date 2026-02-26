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
        print(f"Navigating to {url}...")
        page.goto(url)
        
        print("Waiting for page load (10s)...")
        time.sleep(10) # Wait for CF challenge or dynamic content
        
        print(f"Page Title: {page.title()}")
        
        # Check for year buttons or dropdowns
        years_2024 = page.locator('text=2024').all()
        print(f"Found {len(years_2024)} elements with text '2024'")
        years_2025 = page.locator('text=2025').all()
        print(f"Found {len(years_2025)} elements with text '2025'")

        # List all buttons/links
        buttons = page.locator('button, a').all()
        print(f"Total buttons/links: {len(buttons)}")
        
        print("--- Links/Buttons Content ---")
        count = 0
        for i, btn in enumerate(buttons): 
            try:
                txt = btn.inner_text().strip()
                # filter empty or very short text unless it's a number
                if len(txt) > 1 :
                    print(f"Item {i}: {txt}")
                    count += 1
                    if count >= 50: break
            except:
                pass

        browser.close()

if __name__ == "__main__":
    inspect()
