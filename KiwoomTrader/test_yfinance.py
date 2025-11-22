import yfinance as yf
import pandas as pd

symbol = "005930.KS"
period = "5d"
interval = "1m"

print(f"Downloading {symbol} with period={period}, interval={interval}...")
try:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    
    print(f"Result shape: {df.shape}")
    if not df.empty:
        print(df.head())
        print(df.tail())
    else:
        print("Data is empty.")
        
except Exception as e:
    print(f"Error: {e}")
