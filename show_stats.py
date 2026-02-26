import pandas as pd

# 讀取 Excel 文件
df = pd.read_excel('downloads/boxoffice_20260212_181452.xlsx', skiprows=1)

print("\n" + "="*100)
print("📊 台灣週票房數據統計摘要 (2026-02-02 到 2026-02-08)")
print("="*100)

# 清理數據 - 移除逗號並轉換為數字
df['金額_數字'] = df['金額'].astype(str).str.replace(',', '').astype(float)
df['票數_數字'] = df['票數'].astype(str).str.replace(',', '').astype(float)

print(f"\n📌 基本統計:")
print(f"   總共電影數: {len(df)} 部")
print(f"   總票房金額: NT$ {df['金額_數字'].sum():,.0f}")
print(f"   總售票數: {df['票數_數字'].sum():,.0f} 張")
print(f"   平均每部電影票房: NT$ {df['金額_數字'].mean():,.0f}")
print(f"   平均每部電影售票: {df['票數_數字'].mean():,.0f} 張")

print(f"\n🏆 TOP 10 票房電影:")
print("="*100)
top10 = df.nlargest(10, '金額_數字')[['序號', '片名', '國別', '金額', '票數', '院數']]
print(top10.to_string(index=False))

print(f"\n🌍 國家/地區分布:")
print("="*100)
country_stats = df.groupby('國別').agg({
    '金額_數字': 'sum',
    '票數_數字': 'sum',
    '片名': 'count'
}).round(0)
country_stats.columns = ['總票房', '總票數', '電影數']
country_stats = country_stats.sort_values('總票房', ascending=False)
print(country_stats.head(10).to_string())

print("\n" + "="*100)
