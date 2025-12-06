import pandas as pd
import os

DATA_FILE = "data/historical_data_2020.csv"

def verify_data():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        return

    print(f"Loading {DATA_FILE}...")
    try:
        # Load only necessary columns to save memory if file is huge
        df = pd.read_csv(DATA_FILE, usecols=['Date', 'Code', 'Name', 'Close', 'Open', 'High', 'Low', 'Volume'], dtype={'Code': str})
        
        print(f"Total rows: {len(df)}")
        
        # Check for Zero Prices
        zero_close = df[df['Close'] <= 0]
        zero_open = df[df['Open'] <= 0]
        zero_high = df[df['High'] <= 0]
        zero_low = df[df['Low'] <= 0]
        
        print("\n[Zero Price Check]")
        print(f"Rows with Close <= 0: {len(zero_close)}")
        print(f"Rows with Open <= 0: {len(zero_open)}")
        print(f"Rows with High <= 0: {len(zero_high)}")
        print(f"Rows with Low <= 0: {len(zero_low)}")
        
        if not zero_close.empty:
            print("\nExamples of Zero Close:")
            print(zero_close.head(10))
            
            print("\nTop affected tickers:")
            print(zero_close['Code'].value_counts().head(5))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_data()
