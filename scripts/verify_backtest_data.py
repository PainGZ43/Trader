import pandas as pd
import os
from datetime import datetime

def load_data_from_csv(symbol, start_date, end_date):
    """
    Load data from local CSV file.
    """
    csv_path = os.path.join("data", "historical_data_2020.csv")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return None
        
    try:
        print(f"Loading CSV data from {csv_path}...")
        # Ensure Code is string to match symbol
        df = pd.read_csv(csv_path, dtype={'Code': str}) 
        df['Date'] = pd.to_datetime(df['Date'])
        
        print(f"Total rows in CSV: {len(df)}")
        print(f"Unique symbols: {df['Code'].nunique()}")
        
        # Filter by Symbol
        df_sym = df[df['Code'] == symbol].copy()
        if df_sym.empty:
            print(f"No data found for symbol {symbol}")
            return pd.DataFrame()
            
        # Filter by Date
        # start_date, end_date are strings "YYYYMMDD"
        s_date = datetime.strptime(start_date, "%Y%m%d")
        e_date = datetime.strptime(end_date, "%Y%m%d")
        
        mask = (df_sym['Date'] >= s_date) & (df_sym['Date'] <= e_date)
        df_sym = df_sym.loc[mask]
        
        # Rename columns to match what Backtester expects (lowercase)
        # CSV: Date, Code, Name, Open, High, Low, Close, Volume
        # Expected: timestamp, open, high, low, close, volume
        df_sym = df_sym.rename(columns={
            "Date": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        
        df_sym.set_index('timestamp', inplace=True)
        df_sym.sort_index(inplace=True)
        
        return df_sym
        
    except Exception as e:
        print(f"Failed to load CSV: {e}")
        return None

if __name__ == "__main__":
    # Test with a known symbol (e.g., Samsung Electronics 005930)
    symbol = "005930"
    start_date = "20230101"
    end_date = "20251231"
    
    print(f"Testing load for {symbol} ({start_date} ~ {end_date})...")
    df = load_data_from_csv(symbol, start_date, end_date)
    
    if df is not None and not df.empty:
        print("Success!")
        print(df.head())
        print(df.tail())
        print(f"Loaded {len(df)} rows.")
    else:
        print("Failed to load data or empty result.")
