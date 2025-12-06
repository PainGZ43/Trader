from pykrx import stock
import pandas as pd
from datetime import datetime
import os

def download_index_data():
    today = datetime.now().strftime("%Y%m%d")
    start_date = "20200101"
    
    indices = {
        "1001": "KOSPI",
        "2001": "KOSDAQ"
    }
    
    all_data = []
    
    print("Downloading Index Data...")
    
    for ticker, name in indices.items():
        print(f"Fetching {name} ({ticker})...")
        try:
            df = stock.get_index_ohlcv(start_date, today, ticker)
            df = df.reset_index()
            df["종목코드"] = ticker
            df["종목명"] = name
            
            # Standardize columns
            # pykrx index columns: 날짜, 시가, 고가, 저가, 종가, 거래량, 거래대금, 상장시가총액...
            
            target_cols = ["날짜", "종목명", "종목코드", "시가", "고가", "저가", "종가", "거래량"]
            
            # Rename if necessary (pykrx usually returns Korean)
            # Just in case, let's map
            rename_map = {
                "날짜": "Date",
                "시가": "Open",
                "고가": "High",
                "저가": "Low",
                "종가": "Close",
                "거래량": "Volume"
            }
            
            # Filter available columns
            available_cols = [c for c in target_cols if c in df.columns]
            df = df[available_cols]
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = final_df.sort_values(by=["날짜", "종목코드"])
        
        output_file = "data/market_index_data_2020.csv"
        final_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"Saved {len(final_df)} rows to {output_file}")
    else:
        print("No data fetched.")

if __name__ == "__main__":
    download_index_data()
