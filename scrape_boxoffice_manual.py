"""
Taiwan Box Office Data Scraper - Playwright Version with Stealth
Uses Playwright with stealth mode to handle JavaScript-rendered content
"""

import os
import time
from playwright.sync_api import sync_playwright
import pandas as pd

def scrape_boxoffice_data():
    """
    Scrape Taiwan box office data using Playwright with stealth techniques
    """
    
    # Try multiple URLs
    urls = [
        "https://boxofficetw.tfai.org.tw/boxOffice/weekly",
        "https://boxofficetw.tfai.org.tw/statistic",
        "https://www.tfi.org.tw/"
    ]
    
    # Create downloads folder
    downloads_folder = os.path.abspath("downloads")
    os.makedirs(downloads_folder, exist_ok=True)
    
    print("台灣電影票房數據爬蟲 (Playwright Stealth 版本)")
    print("="*80)
    
    try:
        with sync_playwright() as p:
            # Launch browser with more realistic settings
            print("\n正在啟動瀏覽器...")
            browser = p.chromium.launch(
                headless=False,  # Use visible browser to avoid detection
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Create context with realistic settings
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-TW',
                timezone_id='Asia/Taipei'
            )
            
            # Add init script to hide webdriver
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = context.new_page()
            
            # Try each URL
            for url in urls:
                print(f"\n嘗試訪問: {url}")
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait a bit for any redirects or loading
                    time.sleep(3)
                    
                    # Check if we hit Cloudflare block
                    page_content = page.content()
                    if 'Cloudflare' in page_content and 'blocked' in page_content.lower():
                        print("❌ 被 Cloudflare 阻擋")
                        continue
                    
                    print("✓ 頁面載入成功")
                    
                    # Save screenshot
                    screenshot_path = os.path.join(downloads_folder, "page_screenshot.png")
                    page.screenshot(path=screenshot_path)
                    print(f"✓ 已儲存截圖: {screenshot_path}")
                    
                    # Save HTML
                    debug_path = os.path.join(downloads_folder, f"page_{urls.index(url)}.html")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    print(f"✓ 已儲存 HTML: {debug_path}")
                    
                    # Look for download links or buttons
                    print("\n尋找下載元素...")
                    
                    # Try to find Excel links
                    xlsx_links = page.locator('a[href*=".xlsx"]').all()
                    if xlsx_links:
                        print(f"✓ 找到 {len(xlsx_links)} 個 Excel 連結")
                        break
                    
                    # Try to find download buttons with Chinese text
                    download_elements = page.locator('button:has-text("下載"), a:has-text("下載"), button:has-text("Excel")').all()
                    if download_elements:
                        print(f"✓ 找到 {len(download_elements)} 個下載按鈕")
                        break
                    
                    print("⚠ 未找到下載元素，嘗試下一個 URL")
                    
                except Exception as e:
                    print(f"✗ 錯誤: {e}")
                    continue
            
            # If we successfully loaded a page, try to download
            print("\n請手動操作：")
            print("1. 瀏覽器視窗已開啟")
            print("2. 請在瀏覽器中手動點擊下載按鈕")
            print("3. 下載完成後，請將檔案移動到 'downloads' 資料夾")
            print("4. 按 Enter 繼續...")
            
            # Wait for user input
            input()
            
            browser.close()
            
            # Look for downloaded Excel file
            print("\n尋找下載的檔案...")
            excel_files = [f for f in os.listdir(downloads_folder) if f.endswith(('.xlsx', '.xls'))]
            
            if not excel_files:
                print("✗ 未找到 Excel 檔案")
                return None
            
            # Use the newest file
            excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(downloads_folder, x)), reverse=True)
            latest_file = excel_files[0]
            filepath = os.path.join(downloads_folder, latest_file)
            
            print(f"✓ 找到檔案: {latest_file}")
            
            # Parse the Excel file
            print("\n" + "="*80)
            print("解析 Excel 檔案...")
            print("="*80)
            
            df = None
            for skip_rows in [0, 1, 2, 3, 4]:
                try:
                    temp_df = pd.read_excel(filepath, skiprows=skip_rows)
                    columns_str = ' '.join([str(col) for col in temp_df.columns])
                    if '中文片名' in columns_str or '片名' in columns_str or '銷售金額' in columns_str:
                        df = temp_df
                        print(f"✓ 找到標題列於第 {skip_rows + 1} 行")
                        break
                except:
                    continue
            
            if df is None:
                df = pd.read_excel(filepath)
            
            df = df.dropna(how='all')
            
            print("\n" + "="*80)
            print("前 5 筆資料：")
            print("="*80)
            print(df.head(5).to_string(index=False))
            
            print("\n" + "="*80)
            print(f"資料維度: {df.shape[0]} 列 × {df.shape[1]} 欄")
            print(f"\n欄位：")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")
            
            print("\n" + "="*80)
            print("✓ 數據解析完成！")
            print("="*80)
            
            return df
            
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = scrape_boxoffice_data()
