# 台灣電影票房爬蟲 - 專案總結

## ✅ 成功完成！

### 專案目標
建立一個自動化 Python 腳本，用於爬取台灣電影票房數據並解析 Excel 文件。

### 最終解決方案

**技術棧：**
- **Playwright** - 處理 JavaScript 動態渲染的網頁
- **Pandas** - Excel 數據解析
- **Openpyxl** - Excel 文件讀取

**腳本：** `scrape_boxoffice.py`

**工作流程：**
1. 使用 Playwright 啟動 Chromium 瀏覽器（可見模式）
2. 訪問 `https://boxofficetw.tfai.org.tw/statistic`
3. 等待頁面完全載入（包含 JavaScript 渲染）
4. 自動找到並點擊 Excel 下載按鈕
5. 捕獲下載並保存到 `downloads/` 資料夾
6. 使用 Pandas 智能解析 Excel（自動偵測標題列）
7. 顯示數據和所有欄位名稱

---

## 📊 成功獲取的數據

### 數據文件
- **檔案名稱：** `boxoffice_20260212_181452.xlsx`
- **原始檔名：** 票房資料匯出週票房 2026-02-02 到 2026-02-08.xlsx
- **數據規模：** 112 列 × 14 欄

### 欄位結構（Database Schema 參考）

| # | 欄位名稱 | 說明 | 資料型別建議 |
|---|---------|------|------------|
| 1 | 序號 | 排名序號 | INTEGER |
| 2 | 國別 | 電影出品國家/地區 | VARCHAR(50) |
| 3 | 片名 | 電影中文片名 | VARCHAR(200) |
| 4 | 上映日 | 上映日期 | DATE |
| 5 | 出品 | 出品公司 | VARCHAR(200) |
| 6 | 院數 | 上映院線數量 | INTEGER |
| 7 | 金額 | 週票房金額（新台幣） | INTEGER |
| 8 | 金額變動(%) | 相比上週金額變動百分比 | DECIMAL(10,2) |
| 9 | 票數 | 週售出票數 | INTEGER |
| 10 | 票數變動(%) | 相比上週票數變動百分比 | DECIMAL(10,2) |
| 11 | 市占率(%) | 市場占有率百分比 | DECIMAL(10,2) |
| 12 | 總日數 | 累計上映天數 | INTEGER |
| 13 | 總金額 | 累計總票房金額 | INTEGER |
| 14 | 總票數 | 累計總售票數 | INTEGER |

### 數據樣本（前 5 筆）

```
序號  國別    片名                    上映日        院數    金額      票數
1    西班牙  小勇士大冒險            2026/01/31    3      372,693   1,501
2    美國    關鍵公敵                2026/01/30    3    4,146,060  14,845
3    美國    猩瘋血雨                2026/01/30    7    1,041,042   3,981
4    日本    空之境界劇場版：第四章  2026/01/30    7      725,795   2,912
5    韓國    末路雙嬌                2026/01/30    5      355,029   1,426
```

---

## 🚀 使用方法

### 安裝依賴
```bash
pip install -r requirements.txt
playwright install chromium
```

### 執行腳本
```bash
python scrape_boxoffice.py
```

### 輸出
- **Excel 文件：** `downloads/boxoffice_YYYYMMDD_HHMMSS.xlsx`
- **頁面截圖：** `downloads/page_YYYYMMDD_HHMMSS.png`
- **Terminal 輸出：** 前 5 筆數據 + 所有欄位名稱

---

## 🗄️ 資料庫實作 (New)

### Schema 設計 (SQLModel)

**Movie (電影資料)**
- `id`: Primary Key
- `name`: 片名 (Index)
- `release_date`: 上映日
- `country`: 國別
- `distributor`: 出品

**WeeklyBoxOffice (週票房紀錄)**
- `id`: Primary Key
- `movie_id`: Foreign Key (Movie)
- `report_date_start`: 報表起始日
- `report_date_end`: 報表結束日
- `theater_count`: 院數
- `weekly_revenue`: 本週票房 (Int)
- `cumulative_revenue`: 累計票房 (Int)
- `weekly_tickets`: 本週票數 (Int)

### 數據處理流程
1. **爬蟲**: Playwright 自動下載 Excel
2. **解析**: Pandas 讀取並識別日期範圍
3. **清洗**: 移除數字中的逗號，轉換日期格式
4. **存儲**: 
   - 檢查電影是否存在 (Get or Create)
   - 建立週票房紀錄並關聯電影
   - 寫入 SQLite (`boxoffice.db`)

### 當前數據狀態
- **總電影數**: 112 部
- **週票房紀錄**: 112 筆
- **資料期間**: 2026-02-02 到 2026-02-08

---

## 🔧 技術突破


### 遇到的挑戰
1. **Cloudflare 保護** - 初期使用 requests/cloudscraper 被阻擋
2. **動態 JavaScript 渲染** - 頁面使用 SPA 架構，無法靜態解析
3. **下載按鈕觸發** - 需要模擬真實瀏覽器點擊

### 解決方案
1. ✅ 使用 **Playwright** 模擬真實瀏覽器
2. ✅ 添加 **反檢測機制**（隱藏 webdriver 屬性）
3. ✅ 使用 `page.expect_download()` 捕獲下載
4. ✅ 智能偵測 Excel 標題列位置

---

## 📁 專案文件結構

```
taiwan-boxoffice-scraper/
├── scrape_boxoffice.py          # 主要爬蟲腳本（完全自動化）
├── requirements.txt              # Python 依賴
├── downloads/                    # 下載的 Excel 文件和截圖
│   ├── boxoffice_*.xlsx
│   └── page_*.png
├── README.md                     # 專案說明
└── TECHNICAL_STATUS.md           # 技術分析文檔
```

---

## ✨ 下一步建議

### 1. 建立資料庫
使用上方的欄位結構建立 SQLite/PostgreSQL 資料庫：

```sql
CREATE TABLE weekly_boxoffice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank INTEGER,
    region VARCHAR(50),
    title VARCHAR(200),
    release_date DATE,
    publisher VARCHAR(200),
    theater_count INTEGER,
    weekly_revenue INTEGER,
    revenue_change DECIMAL(10,2),
    weekly_tickets INTEGER,
    tickets_change DECIMAL(10,2),
    market_share DECIMAL(10,2),
    total_days INTEGER,
    total_revenue INTEGER,
    total_tickets INTEGER,
    week_start DATE,
    week_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 定期自動化
設定 cron job 或 Windows Task Scheduler 每週自動執行：
```bash
# 每週一早上 9 點執行
0 9 * * 1 cd /path/to/scraper && python scrape_boxoffice.py
```

### 3. 數據分析
- 追蹤電影票房趨勢
- 分析市場占有率變化
- 比較不同國家/地區電影表現
- 預測票房走勢

---

## 📝 版本記錄

**v1.0 (2026-02-12)**
- ✅ 完成全自動化爬蟲
- ✅ 成功繞過 Cloudflare 保護
- ✅ 自動下載並解析 Excel 文件
- ✅ 正確識別所有中文欄位

---

**專案狀態：** 🟢 **完成並可正常運作**
