import pandas as pd
import os

file_path = r"e:\GitHub\Trader\PainTrader\docs\키움 REST API 문서.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheets: {xls.sheet_names}")
    
    target_sheet = None
    for name in xls.sheet_names:
        if "ka10086" in name:
            target_sheet = name
            break
            
    if target_sheet:
        print(f"\n--- Reading Sheet: {target_sheet} ---")
        df = pd.read_excel(xls, sheet_name=target_sheet)
        # Print rows 40-60 where examples usually are
        print(df.iloc[40:60].to_string())
    else:
        print("Sheet ka10086 not found.")
            
except Exception as e:
    print(f"Error opening file: {e}")
