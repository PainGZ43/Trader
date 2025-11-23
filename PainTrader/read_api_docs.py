import pandas as pd
import os

file_path = r"e:\GitHub\Trader\PainTrader\docs\키움 REST API 문서.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheets: {xls.sheet_names}")
    
    keywords = ["ka10004", "주식호가", "WebSocket", "웹소켓", "Base URL", "도메인", "oauth"]
    
    for sheet_name in xls.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            # Convert to string for searching
            df_str = df.astype(str)
            
            for keyword in keywords:
                mask = df_str.apply(lambda x: x.str.contains(keyword, case=False, na=False)).any(axis=1)
                if mask.any():
                    print(f"Found '{keyword}':")
                    print(df[mask].to_string())
                    
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {e}")
            
except Exception as e:
    print(f"Error opening file: {e}")
