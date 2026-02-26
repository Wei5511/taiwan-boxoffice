# Taiwan Box Office Data Scraper

A Python script to download and parse weekly box office statistics from the Taiwan Film Institute (TFI) website.

## Features

- **Direct Excel download** from TFI using predictable URL patterns (no HTML scraping needed)
- Automatically calculates Monday-Sunday weeks for any given date
- Downloads Excel files to a local `downloads` folder with caching
- Intelligently detects and skips header rows in Excel files
- Parses data with pandas and displays top 5 rows with column analysis
- Handles SSL verification issues
- Comprehensive error handling for HTTP errors and timeouts

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Fetch Last Week's Data (Default)

Run the script without arguments to fetch data from last week:
```bash
python scrape_boxoffice.py
```

### Fetch Specific Week's Data

Use the example script to fetch a specific week:
```bash
python example_fetch.py
```

Or modify the script to use your own date:
```python
from scrape_boxoffice import scrape_boxoffice_data
from datetime import datetime

# Fetch data for the week containing January 1, 2024
df = scrape_boxoffice_data(datetime(2024, 1, 1))
```

The script will:
1. Calculate the Monday-Sunday week containing your specified date
2. Construct the TFI Excel file URL
3. Download the file to the `downloads` folder (skips if already cached)
4. Parse the Excel file with pandas
5. Print the top 5 rows and identify key columns

## Expected Data Columns

The script automatically identifies common Taiwanese box office columns:
- **中文片名** - Movie Name (Chinese)
- **銷售金額** - Revenue
- **上映院數** - Theater Count
- **累計銷售金額** - Cumulative Revenue

## How It Works

Unlike typical web scrapers that parse HTML, this script uses **direct downloads**:

1. **URL Pattern**: TFI stores weekly reports in a predictable format:
   ```
   https://www.tfi.org.tw/Content/TFI/PublicInfo/全國電影票房{year}年{MMDD}-{MMDD}統計資訊.xlsx
   ```

2. **Date Calculation**: The script finds the Monday-Sunday week for any date

3. **Smart Parsing**: Automatically detects header rows by searching for key column names

## Troubleshooting

### Connection Timeouts
If you see `ConnectTimeoutError` or `Max retries exceeded`:
- The TFI website (`www.tfi.org.tw`) may be experiencing downtime
- Try again later or check the website status manually
- The website may have geographical restrictions

### 404 File Not Found
If you see `404 File not found`:
- The Excel file for that specific week may not exist yet
- Try fetching an earlier week
- Very recent weeks may not be published yet (TFI typically publishes data with a delay)

### Missing Columns
If expected columns aren't found:
- TFI occasionally changes their Excel format
- Check the printed column list to see what's available
- The script still parses and displays all data

## Notes

- Downloads are cached in the `downloads` directory to avoid redundant requests
- SSL verification is disabled to handle potential certificate issues
- Header detection tries multiple skip-row values (0-4) to find the correct starting point
- Based on the working approach from the `taiwan-box-office` Next.js project

