import pandas as pd

# 讀取 Excel 文件
df = pd.read_excel('downloads/boxoffice_20260212_181452.xlsx', skiprows=1)

# 顯示完整數據
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', None)

print("="*100)
print("台灣週票房數據 (2026-02-02 到 2026-02-08)")
print("="*100)
print(f"\n總共 {len(df)} 部電影\n")
print(df.to_string(index=False))
print("\n" + "="*100)
print("數據統計摘要:")
print("="*100)
print(f"總票房金額: NT$ {df['金額'].sum():,}")
print(f"總售票數: {df['票數'].sum():,} 張")
print(f"平均每部電影票房: NT$ {df['金額'].mean():,.0f}")
print(f"最高票房電影: {df.loc[df['金額'].idxmax(), '片名']} (NT$ {df['金額'].max():,})")
