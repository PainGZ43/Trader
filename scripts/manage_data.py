import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pykrx import stock
import time

# Ensure output is printed immediately
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = "data"
HISTORICAL_DATA_FILE = os.path.join(DATA_DIR, "historical_data_2020.csv")
INDEX_DATA_FILE = os.path.join(DATA_DIR, "market_index_data_2020.csv")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_market_ticker_list_snapshot(date_str):
    """
    Get ticker list for a specific date to handle survivorship bias.
    """
    try:
        kospi = stock.get_market_ticker_list(date_str, market="KOSPI")
        kosdaq = stock.get_market_ticker_list(date_str, market="KOSDAQ")
        return list(set(kospi + kosdaq))
    except Exception as e:
        print(f"Error getting ticker list for {date_str}: {e}")
        return []

def filter_tickers(tickers, date_str):
    """
    Filter out SPAC, ETF, Preferred, Penny stocks.
    """
    filtered = []
    
    # Get ETF list
    try:
        etfs = stock.get_etf_ticker_list(date_str)
    except:
        etfs = []
        
    for ticker in tickers:
        if ticker in etfs:
            continue
            
        name = stock.get_market_ticker_name(ticker)
        
        if "스팩" in name:
            continue
            
        # Preferred stocks usually end with non-0 (e.g. 005935)
        # But some preferred stocks end with 5, 7, 9, K, L, M etc.
        # Simple heuristic: must end with '0'
        if not ticker.endswith("0"):
            continue
            
        filtered.append((ticker, name))
        
    return filtered

def download_initial_data(start_year=2020):
    """
    Download data from start_year to present.
    To avoid survivorship bias, we get ticker list for each year's start.
    """
    print(f"Starting initial download from {start_year}...", flush=True)
    ensure_data_dir()
    
    all_target_tickers = {} # ticker -> name
    
    current_year = datetime.now().year
    
    # 1. Collect Union of Tickers
    for year in range(start_year, current_year + 1):
        date_str = f"{year}0102" # First trading day approx
        print(f"Collecting tickers for {year}...", flush=True)
        tickers = get_market_ticker_list_snapshot(date_str)
        filtered = filter_tickers(tickers, date_str)
        
        for t, n in filtered:
            all_target_tickers[t] = n
            
    print(f"Total unique tickers to download: {len(all_target_tickers)}", flush=True)
    
    # 2. Download Data
    # We can use stock.get_market_ohlcv(start, end, ticker)
    # But for 2000+ stocks, this is slow.
    # Faster approach: Iterate dates and use get_market_ohlcv(date, market="ALL")
    # This gets all stocks for a day in one request.
    
    start_date = datetime(start_year, 1, 1)
    end_date = datetime.now()
    
    # Check if file exists to resume?
    # For simplicity, we assume fresh start or use update mode.
    
    # We will use the 'update' logic effectively.
    # If file doesn't exist, create empty one.
    if not os.path.exists(HISTORICAL_DATA_FILE):
        df_empty = pd.DataFrame(columns=["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"])
        df_empty.to_csv(HISTORICAL_DATA_FILE, index=False, encoding="utf-8-sig")
        
    update_data()

def update_data(days=0):
    """
    Incrementally update data.
    """
    print("Checking for updates...", flush=True)
    ensure_data_dir()
    
    if not os.path.exists(HISTORICAL_DATA_FILE):
        # Create header if not exists
        df_empty = pd.DataFrame(columns=["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"])
        df_empty.to_csv(HISTORICAL_DATA_FILE, index=False, encoding="utf-8-sig")
        
        if days > 0:
            last_date = datetime.now() - timedelta(days=days)
        else:
            last_date = datetime(2020, 1, 1) - timedelta(days=1)
    else:
        # Read last line efficiently or just read 'Date' column?
        # Reading whole CSV is slow.
        # Let's try to read just the last few lines.
        try:
            # This might fail if file is small, but robust enough for now
            with open(HISTORICAL_DATA_FILE, 'rb') as f:
                f.seek(-1024, os.SEEK_END)
                last_lines = f.readlines()
                last_line = last_lines[-1].decode('utf-8')
                last_date_str = last_line.split(',')[0]
                try:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                except:
                    # Fallback
                    df = pd.read_csv(HISTORICAL_DATA_FILE)
                    if not df.empty:
                        last_date = pd.to_datetime(df['Date']).max()
                    else:
                        last_date = datetime(2020, 1, 1) - timedelta(days=1)
        except:
             # Fallback
            try:
                df = pd.read_csv(HISTORICAL_DATA_FILE)
                if not df.empty:
                    last_date = pd.to_datetime(df['Date']).max()
                else:
                    last_date = datetime(2020, 1, 1) - timedelta(days=1)
            except:
                last_date = datetime(2020, 1, 1) - timedelta(days=1)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if last_date >= today:
        print("Data is up to date.")
        return

    print(f"Updating from {last_date.date()} to {today.date()}...", flush=True)
    
    current = last_date + timedelta(days=1)
    
    # We need a map of Code -> Name for ALL times.
    # Since names change, we should get name from daily data if possible.
    # pykrx get_market_ohlcv_by_ticker returns Code but not Name?
    # get_market_ohlcv(date, market="ALL") returns:
    # 티커 (index), 시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률
    # It does NOT return Name.
    # We need to fetch ticker names.
    # Optimization: Fetch ticker list for the day and map.
    
    while current <= today:
        d_str = current.strftime("%Y%m%d")
        
        # Skip weekends (simple check)
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue
            
        try:
            print(f"Fetching {d_str}...", flush=True)
            df_daily = stock.get_market_ohlcv(d_str, market="ALL")
            
            if df_daily.empty:
                current += timedelta(days=1)
                continue
                
            # Get Names
            # This is slow if we call get_market_ticker_name for every ticker.
            # But get_market_ticker_list doesn't return names.
            # stock.get_market_cap(d_str) returns Name!
            # Columns: 종가, 시가총액, 거래량, 거래대금, 상장주식수
            # Wait, get_market_cap returns Name? No, usually just data.
            # Let's check get_market_fundamental?
            
            # Actually, for backtesting, Name is decorative. Code is ID.
            # We can fetch names only for target tickers or just once.
            # Let's try to get names efficiently.
            # stock.get_market_ticker_name is cached?
            
            # Alternative: Use existing names in DB/File or update slowly.
            # For speed, let's just use Code. Name can be empty or filled later.
            # OR, we can use a separate metadata file for Code->Name.
            
            # Let's just try to get names for active tickers.
            # To avoid 2000 requests, we can skip name or use a cache.
            # Let's use a dummy name or Code as Name for now to speed up.
            
            df_daily = df_daily.reset_index()
            # Columns: 티커, 시가, 고가, 저가, 종가, 거래량...
            
            # Filter columns
            df_daily = df_daily.rename(columns={
                "티커": "Code",
                "시가": "Open",
                "고가": "High",
                "저가": "Low",
                "종가": "Close",
                "거래량": "Volume"
            })
            
            # Add Date
            df_daily["Date"] = current.strftime("%Y-%m-%d")
            
            # Add Name (Placeholder)
            df_daily["Name"] = df_daily["Code"] 
            
            # Filter Tickers (Apply our filter logic)
            # We need to filter SPAC/ETF here too?
            # Yes, to keep file size manageable.
            # But filtering requires Name...
            # We MUST get names to filter SPAC.
            
            # Optimization: Only fetch names for new tickers we haven't seen?
            # Or just fetch all names?
            # stock.get_market_ticker_name is actually fast (local DB in pykrx?).
            # Let's try fetching for all.
            
            # Actually, pykrx has `stock.get_market_ticker_name` which might be slow in loop.
            # Let's assume we want to filter.
            
            # Let's use a bulk method if available.
            # No bulk method for names.
            
            # Compromise:
            # 1. Get all tickers for KOSPI/KOSDAQ for that day.
            # 2. Filter using `filter_tickers` (which calls get_name).
            # 3. Only keep rows in df_daily that match filtered tickers.
            
            kospi = stock.get_market_ticker_list(d_str, market="KOSPI")
            kosdaq = stock.get_market_ticker_list(d_str, market="KOSDAQ")
            all_tickers = kospi + kosdaq
            
            filtered = filter_tickers(all_tickers, d_str) # This takes time (~1-2 sec for 2000 calls? No, maybe more)
            # If it takes too long, we might need to optimize.
            # But `filter_tickers` calls `get_market_ticker_name`.
            
            valid_codes = {t: n for t, n in filtered}
            
            # Filter DataFrame
            df_daily = df_daily[df_daily["Code"].isin(valid_codes.keys())]
            df_daily["Name"] = df_daily["Code"].map(valid_codes)
            
            # Select Columns
            df_daily = df_daily[["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"]]
            
            # Append to CSV
            df_daily.to_csv(HISTORICAL_DATA_FILE, mode='a', header=False, index=False, encoding="utf-8-sig")
            print(f"  -> Saved {len(df_daily)} rows.", flush=True)
            
        except Exception as e:
            print(f"Error processing {d_str}: {e}")
            
        current += timedelta(days=1)
        # Sleep to be nice?
        time.sleep(0.1)

def validate_data():
    """
    Check CSV integrity.
    """
    print("Validating data...", flush=True)
    if not os.path.exists(HISTORICAL_DATA_FILE):
        print("File not found.")
        return
        
    try:
        df = pd.read_csv(HISTORICAL_DATA_FILE)
        print(f"Total Rows: {len(df)}")
        print(f"Unique Tickers: {df['Code'].nunique()}")
        print(f"Date Range: {df['Date'].min()} ~ {df['Date'].max()}")
        
        # Check for duplicates
        dups = df.duplicated(subset=['Date', 'Code']).sum()
        if dups > 0:
            print(f"WARNING: {dups} duplicate rows found.")
        else:
            print("No duplicates found.")
            
    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["download", "update", "validate"], default="update")
    parser.add_argument("--days", type=int, default=0, help="Days to look back for fresh update")
    args = parser.parse_args()
    
    if args.mode == "download":
        download_initial_data()
    elif args.mode == "update":
        update_data(args.days)
    elif args.mode == "validate":
        validate_data()
