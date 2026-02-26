"""
Taiwan Box Office Data Scraper - Fully Automated with Playwright
Automatically downloads Excel files, parses them, and saves to SQLite database
"""

import os
import time
import re
from datetime import datetime, date
from playwright.sync_api import sync_playwright
import pandas as pd
from sqlmodel import Session, select
from models import Movie, WeeklyBoxOffice
from database import engine, create_db_and_tables

def save_to_database(df, start_date, end_date):
    """
    Save DataFrame to SQLite database using SQLModel
    """
    if df is None:
        return

    print("\n" + "="*80)
    print("Saving to Database...")
    print("="*80)
    
    create_db_and_tables()
    
    with Session(engine) as session:
        for index, row in df.iterrows():
            try:
                # 1. Clean Data
                def clean_int(val):
                    if pd.isna(val):
                        return None
                    if isinstance(val, (int, float)):
                        return int(val)
                    if isinstance(val, str):
                        return int(val.replace(',', '').replace(' ', ''))
                    return None
                
                name = row.get('片名') or row.get('中文片名')
                if not name:
                    continue
                    
                # Parse release date
                release_date_raw = row.get('上映日')
                release_date = None
                if pd.notna(release_date_raw):
                    if isinstance(release_date_raw, datetime):
                        release_date = release_date_raw.date()
                    elif isinstance(release_date_raw, str):
                        try:
                            release_date = datetime.strptime(release_date_raw, '%Y/%m/%d').date()
                        except:
                            try:
                                release_date = datetime.strptime(release_date_raw, '%Y-%m-%d').date()
                            except:
                                pass
                
                # Get or Create Movie
                statement = select(Movie).where(Movie.name == name)
                results = session.exec(statement)
                movie = results.first()
                
                if not movie:
                    movie = Movie(
                        name=name,
                        release_date=release_date,
                        country=row.get('國別'),
                        distributor=row.get('出品')
                    )
                    session.add(movie)
                    session.commit()
                    session.refresh(movie)
                
                # Create Weekly Record
                weekly_record = WeeklyBoxOffice(
                    movie_id=movie.id,
                    report_date_start=start_date,
                    report_date_end=end_date,
                    theater_count=clean_int(row.get('院數')),
                    weekly_revenue=clean_int(row.get('金額') or row.get('銷售金額')),
                    cumulative_revenue=clean_int(row.get('總金額')),
                    weekly_tickets=clean_int(row.get('票數') or row.get('銷售票數')),
                    cumulative_tickets=clean_int(row.get('累積票數'))
                )
                session.add(weekly_record)
            
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        session.commit()
        
    print("✓ Database updated successfully!")

def scrape_boxoffice_data():
    """
    Fully automated scraper using Playwright
    """
    
    # Target URL
    url = "https://boxofficetw.tfai.org.tw/statistic"
    
    # Create downloads folder
    downloads_folder = os.path.abspath("downloads")
    os.makedirs(downloads_folder, exist_ok=True)
    
    print("台灣電影票房數據爬蟲 (完全自動化版本 + 資料庫存儲)")
    print("="*80)
    print(f"目標 URL: {url}")
    print(f"下載資料夾: {downloads_folder}")
    print("="*80)
    
    try:
        with sync_playwright() as p:
            print("\n正在啟動瀏覽器...")
            browser = p.chromium.launch(
                headless=False,  # Visible to help with debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # Set download path
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-TW',
                timezone_id='Asia/Taipei'
            )
            
            # Hide webdriver property
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = context.new_page()
            
            print(f"\n正在訪問: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            print("等待頁面完全載入...")
            time.sleep(5)
            
            # Check for Cloudflare block
            if 'blocked' in page.content().lower() and 'cloudflare' in page.content().lower():
                print("❌ 被 Cloudflare 阻擋")
                browser.close()
                return None
            
            print("✓ 頁面載入成功")
            
            # Look for Excel download button
            print("\n尋找 Excel 下載按鈕...")
            
            # Try different selectors for the Excel button
            excel_button = None
            selectors = [
                'button[data-type="Excel"]',
                'button:has-text("Excel")',
                'button[data-ext="xlsx"]',
                'a:has-text("Excel")',
            ]
            
            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        excel_button = page.locator(selector).first
                        print(f"✓ 找到 Excel 按鈕 (使用選擇器: {selector})")
                        break
                except:
                    continue
            
            if not excel_button:
                print("❌ 未找到 Excel 下載按鈕")
                browser.close()
                return None
            
            # Click the Excel button and wait for download
            print("\n正在點擊 Excel 下載按鈕...")
            
            # Use expect_download to capture the download
            with page.expect_download(timeout=30000) as download_info:
                excel_button.click()
                print("✓ 已點擊下載按鈕")
            
            download = download_info.value
            suggested_filename = download.suggested_filename
            print(f"✓ 下載開始: {suggested_filename}")
            
            # Parse dates from filename
            # Filename format: 票房資料匯出週票房 2026-02-02 到 2026-02-08.xlsx
            start_date = None
            end_date = None
            date_match = re.search(r'(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})', suggested_filename)
            if date_match:
                start_date_str = date_match.group(1)
                end_date_str = date_match.group(2)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                print(f"✓ 識別到日期範圍: {start_date} 到 {end_date}")
            else:
                print("⚠ 無法從檔名識別日期，將使用今日日期")
                start_date = date.today()
                end_date = date.today()
            
            # Save to downloads folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"boxoffice_{timestamp}.xlsx"
            filepath = os.path.join(downloads_folder, filename)
            
            download.save_as(filepath)
            print(f"✓ 檔案已儲存: {filepath}")
            
            # Close browser
            browser.close()
            print("\n✓ 瀏覽器已關閉")
            
            # Parse the Excel file
            print("\n" + "="*80)
            print("解析 Excel 檔案...")
            print("="*80)
            
            # Try different skip rows to find the header
            df = None
            for skip_rows in [0, 1, 2, 3, 4]:
                try:
                    temp_df = pd.read_excel(filepath, skiprows=skip_rows)
                    columns_str = ' '.join([str(col) for col in temp_df.columns])
                    
                    # Look for common column keywords
                    if any(keyword in columns_str for keyword in ['片名', '中文片名', '銷售金額', '金額', '票數', '院數']):
                        df = temp_df
                        print(f"✓ 找到標題列於第 {skip_rows + 1} 行（跳過 {skip_rows} 行）")
                        break
                except Exception as e:
                    continue
            
            # If still no valid dataframe, try without skipping
            if df is None:
                print("⚠ 未找到明確標題列，使用預設解析")
                df = pd.read_excel(filepath)
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            # Save to Database
            save_to_database(df, start_date, end_date)
            
            print("\n" + "="*80)
            print("✓ 數據爬取、解析與存儲完成！")
            
            # Summary
            with Session(engine) as session:
                movie_count = session.query(Movie).count()
                record_count = session.query(WeeklyBoxOffice).count()
                print(f"Database updated. Total Movies: {movie_count}, Total Weekly Records: {record_count}")
            print("="*80)
            
            return df
            
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = scrape_boxoffice_data()
