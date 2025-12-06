from pykrx import stock
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Ensure output is printed immediately
sys.stdout.reconfigure(encoding='utf-8')

def download_data():
    print("Starting download script...", flush=True)
    today = datetime.now().strftime("%Y%m%d")
    start_date = "20200101"
    
    print("Getting ticker lists...", flush=True)
    try:
        kospi_tickers = stock.get_market_ticker_list(today, market="KOSPI")
        kosdaq_tickers = stock.get_market_ticker_list(today, market="KOSDAQ")
        all_tickers = kospi_tickers + kosdaq_tickers
        print(f"Total tickers: {len(all_tickers)}", flush=True)
    except Exception as e:
        print(f"Error getting tickers: {e}", flush=True)
        return

    # Get ETF list to exclude
    try:
        etf_tickers = stock.get_etf_ticker_list(today)
    except:
        etf_tickers = []
    
    filtered_tickers = []
    
    print("Filtering tickers...", flush=True)
    for ticker in all_tickers:
        if ticker in etf_tickers:
            continue
            
        name = stock.get_market_ticker_name(ticker)
        
        if "스팩" in name:
            continue
            
        if not ticker.endswith("0"):
            continue
            
        filtered_tickers.append((ticker, name))

    print(f"Tickers after static filters: {len(filtered_tickers)}", flush=True)
    
    print("Checking prices for penny stock filter...", flush=True)
    try:
        df_price = stock.get_market_ohlcv(today, market="ALL")
        final_tickers = []
        for ticker, name in filtered_tickers:
            if ticker in df_price.index:
                close_price = df_price.loc[ticker, "종가"]
                if close_price > 1000:
                    final_tickers.append((ticker, name))
    except Exception as e:
        print(f"Error checking prices: {e}", flush=True)
        final_tickers = filtered_tickers # Fallback

    print(f"Final target tickers: {len(final_tickers)}", flush=True)
    
    output_file = "data/historical_data_2020_filtered.csv"
    
    # Check if we can append or start new
    # For simplicity, let's just write to a list and save periodically
    
    all_data = []
    count = 0
    total = len(final_tickers)
    
    print("Fetching historical data...", flush=True)
    
    for ticker, name in final_tickers:
        count += 1
        if count % 10 == 0:
            print(f"Processing {count}/{total} ({name})", flush=True)
            
        try:
            df = stock.get_market_ohlcv(start_date, today, ticker)
            if df.empty:
                continue
                
            df = df.reset_index()
            df["종목코드"] = ticker
            df["종목명"] = name
            
            # Rename/Select columns
            # pykrx columns: 날짜, 시가, 고가, 저가, 종가, 거래량
            rename_map = {
                "날짜": "Date",
                "시가": "Open",
                "고가": "High",
                "저가": "Low",
                "종가": "Close",
                "거래량": "Volume"
            }
            # Ensure we have the columns we want
            # Sometimes pykrx returns English or Korean depending on locale?
            # Usually Korean.
            
            # Add to list
            all_data.append(df)
            
        except Exception as e:
            print(f"Error fetching {name}: {e}", flush=True)
            
        # Save every 50 stocks to avoid memory issues and data loss
        if count % 50 == 0 and all_data:
            save_chunk(all_data, output_file, count == 50)
            all_data = [] # Clear memory
            
    # Save remaining
    if all_data:
        save_chunk(all_data, output_file, count <= 50 and not os.path.exists(output_file))
        
    print("Download complete.", flush=True)

def save_chunk(data_list, filename, header):
    if not data_list:
        return
    df_chunk = pd.concat(data_list, ignore_index=True)
    
    # Filter columns
    target_cols = ["날짜", "종목명", "종목코드", "시가", "고가", "저가", "종가", "거래량"]
    available_cols = [c for c in target_cols if c in df_chunk.columns]
    df_chunk = df_chunk[available_cols]
    
    mode = 'w' if header else 'a'
    df_chunk.to_csv(filename, mode=mode, index=False, header=header, encoding="utf-8-sig")
    print(f"Saved chunk to {filename}", flush=True)

if __name__ == "__main__":
    download_data()
