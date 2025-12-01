import pandas as pd
import os
import sys

# Set encoding for output
sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r"e:\GitHub\Trader\PainTrader\docs\키움 REST API 문서.xlsx"

def search_excel():
    print(f"Reading Excel: {DOC_PATH}")
    try:
        # Read all sheets
        xls = pd.read_excel(DOC_PATH, sheet_name=None)
        print(f"All Sheets: {list(xls.keys())}")
        
        found = False
        for sheet_name, df in xls.items():
            print(f"\n--- Sheet: {sheet_name} ---")
            
            # Convert to string for searching
            df_str = df.astype(str)
            
            # Search for keywords
            keywords = ["주문", "Order", "TR ID", "API ID", "모의투자", "Mock"]
            
            # Filter rows containing any keyword
            mask = df_str.apply(lambda x: x.str.contains('|'.join(keywords), case=False, na=False)).any(axis=1)
            results = df[mask]
            
            if not results.empty:
                found = True
                print(f"Found {len(results)} rows matching keywords:")
                # Print first few columns to avoid clutter, or specific relevant columns if known
                # Let's print the whole row but limited count
                for idx, row in results.head(20).iterrows():
                    print(f"[Row {idx}] {row.values}")
            else:
                print("No keywords found in this sheet.")
                
    except Exception as e:
        print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    search_excel()
