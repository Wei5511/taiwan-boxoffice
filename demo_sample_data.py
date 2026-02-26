"""
Demo with sample data
Demonstrates the parsing functionality using a sample Excel file
"""

import pandas as pd
import os

# Create a sample DataFrame that mimics TFI box office data structure
sample_data = {
    '中文片名': [
        '功夫熊貓4',
        '沙丘：第二部',
        '龍家轉學日記: 我在台電做公關',
        '神偷奶爸4',
        '腦筋急轉彎2'
    ],
    '銷售金額': [15234567, 12456789, 9876543, 8765432, 7654321],
    '上映院數': [120, 105, 95, 88, 82],
    '累計銷售金額': [45678901, 38765432, 25678901, 18765432, 15234567]
}

df = pd.DataFrame(sample_data)

print("="*80)
print("SAMPLE TAIWAN BOX OFFICE DATA")
print("="*80)
print("\nThis demonstrates the expected format of parsed TFI Excel data.")
print("\n" + "="*80)
print("TOP 5 ROWS:")
print("="*80)
print(df.to_string(index=False))

print("\n" + "="*80)
print(f"DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nColumns found:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print("\n" + "="*80)
print("KEY DATA SAMPLE:")
print("="*80)

print(f"\nMovie Names (Column: '中文片名'):")
print(df['中文片名'].to_string(index=False))

print(f"\nRevenue (Column: '銷售金額'):")
print(df['銷售金額'].to_string(index=False))

print(f"\nTheater Count (Column: '上映院數'):")
print(df['上映院數'].to_string(index=False))

print("\n" + "="*80)
print("✓ This is the expected output format when scraping real data!")
print("="*80)
