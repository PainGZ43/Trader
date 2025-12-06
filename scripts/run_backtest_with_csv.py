import pandas as pd
import numpy as np
import os
import sys
import argparse
from multiprocessing import Pool, cpu_count
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.backtester import EventDrivenBacktester
from strategy.strategies import VolatilityBreakoutStrategy, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandStrategy

# Configuration
DATA_FILE = "data/historical_data_2020.csv"
INDEX_FILE = "data/market_index_data_2020.csv"
RESULT_FILE = "data/backtest_results.csv"
TRADE_LOG_FILE = "data/backtest_trades.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found. Please run 'python scripts/manage_data.py --mode download' first.")
        sys.exit(1)
        
    print(f"Loading data from {DATA_FILE}...", flush=True)
    try:
        # Optimize types
        df = pd.read_csv(DATA_FILE, dtype={'Code': str, 'Name': str})
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def load_index_data():
    if not os.path.exists(INDEX_FILE):
        return None
    df = pd.read_csv(INDEX_FILE)
    
    # Rename columns if Korean
    rename_map = {
        "날짜": "Date",
        "종목명": "Name",
        "종목코드": "Code",
        "시가": "Open",
        "고가": "High",
        "저가": "Low",
        "종가": "Close",
        "거래량": "Volume"
    }
    df = df.rename(columns=rename_map)
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

def get_benchmark_return_from_dict(index_data, start, end, market):
    if market not in index_data:
        return 0.0
    
    df = index_data[market]
    mask = (df['Date'] >= start) & (df['Date'] <= end)
    sub = df[mask]
    
    if sub.empty:
        return 0.0
        
    s = sub.iloc[0]['Close']
    e = sub.iloc[-1]['Close']
    if s == 0: return 0.0
    return (e - s) / s * 100

def run_single_backtest(args):
    ticker, name, group_df, strategy_name, index_df_dict, config = args
    
    try:
        # Preprocess
        df = group_df.copy()
        # Ensure columns are lowercase for backtester
        df.columns = [c.lower() for c in df.columns]
        df = df.set_index('date').sort_index()
        
        if df.empty:
            return None
            
        start_date = df.index[0]
        end_date = df.index[-1]
        
        # Initialize Strategy
        if strategy_name == "VolatilityBreakout":
            strategy = VolatilityBreakoutStrategy("BT_VB", ticker)
        elif strategy_name == "RSI":
            strategy = RSIStrategy("BT_RSI", ticker)
        elif strategy_name == "MA":
            strategy = MovingAverageCrossoverStrategy("BT_MA", ticker)
        elif strategy_name == "BollingerBand":
            strategy = BollingerBandStrategy("BT_BB", ticker)
        else:
            strategy = VolatilityBreakoutStrategy("BT_VB", ticker)
            
        strategy.initialize({}) 
        
        # Run Backtest
        backtester = EventDrivenBacktester()
        backtester.configure(config)
        
        # Calculate Signals
        df_signals = strategy.calculate_signals(df) 

        result = backtester.run(strategy, df)
        
        # Benchmark
        bench_return = get_benchmark_return_from_dict(index_df_dict, start_date, end_date, "KOSPI")
        
        # Add ticker info to trades
        for t in result.trades:
            t['ticker'] = ticker
            t['name'] = name
        
        return {
            "ticker": ticker,
            "name": name,
            "return": result.total_return,
            "mdd": result.mdd,
            "win_rate": result.win_rate,
            "trades_count": len(result.trades),
            "sharpe": result.sharpe_ratio,
            "sortino": result.sortino_ratio,
            "mdd_duration": result.max_drawdown_duration,
            "benchmark_return": bench_return,
            "alpha": result.total_return - bench_return,
            "equity_curve": pd.Series(result.equity_curve, index=df_signals.index),
            "trade_list": result.trades
        }
        
    except Exception as e:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, default="VolatilityBreakout", help="Strategy name")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of stocks to test")
    parser.add_argument("--workers", type=int, default=cpu_count(), help="Number of worker processes")
    parser.add_argument("--commission", type=float, default=0.00015, help="Commission rate (0.00015 = 0.015%)")
    parser.add_argument("--slippage", type=float, default=0.0005, help="Slippage rate (0.0005 = 0.05%)")
    args = parser.parse_args()
    
    print(f"Starting Backtest: {args.strategy}")
    print(f"Config: Commission={args.commission}, Slippage={args.slippage}")
    
    # Load Data
    full_df = load_data()
    index_df = load_index_data()
    
    index_data_dict = {}
    if index_df is not None:
        for m in ["KOSPI", "KOSDAQ"]:
            index_data_dict[m] = index_df[index_df['Name'] == m].sort_values('Date')
    
    grouped = full_df.groupby(["Code", "Name"])
    
    tasks = []
    count = 0
    
    backtest_config = {
        "initial_capital": 10_000_000,
        "commission_rate": args.commission,
        "slippage_rate": args.slippage
    }
    
    for (ticker, name), group in grouped:
        if args.limit > 0 and count >= args.limit:
            break
        tasks.append((ticker, name, group, args.strategy, index_data_dict, backtest_config))
        count += 1
        
    print(f"Processing {len(tasks)} stocks with {args.workers} workers...")
    
    results = []
    with Pool(processes=args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(run_single_backtest, tasks)):
            if res:
                results.append(res)
            if (i+1) % 100 == 0:
                print(f"Done {i+1}/{len(tasks)}", flush=True)
                
    if not results:
        print("No results.")
        return
        
    # Process Results
    final_results = []
    equity_curves = []
    all_trades = []
    
    for r in results:
        r_copy = r.copy()
        if 'equity_curve' in r_copy:
            equity_curves.append(r_copy.pop('equity_curve'))
        if 'trade_list' in r_copy:
            all_trades.extend(r_copy.pop('trade_list'))
            
        final_results.append(r_copy)
        
    res_df = pd.DataFrame(final_results)
    res_df.to_csv(RESULT_FILE, index=False, encoding="utf-8-sig")
    
    # Save Trades
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df.to_csv(TRADE_LOG_FILE, index=False, encoding="utf-8-sig")
        print(f"Saved {len(trades_df)} trades to {TRADE_LOG_FILE}")
    
    print(f"Saved results to {RESULT_FILE}")
    
    # Plotting
    try:
        if equity_curves:
            portfolio_df = pd.concat(equity_curves, axis=1)
            portfolio_df = portfolio_df.fillna(method='ffill')
            portfolio_df = portfolio_df / portfolio_df.iloc[0] * 100
            avg_equity = portfolio_df.mean(axis=1)
            
            plt.figure(figsize=(12, 6))
            plt.plot(avg_equity.index, avg_equity.values, label='Average Portfolio')
            
            if 'KOSPI' in index_data_dict:
                kospi = index_data_dict['KOSPI']
                kospi = kospi[kospi['Date'] >= avg_equity.index[0]]
                kospi = kospi.set_index('Date')['Close']
                kospi = kospi.reindex(avg_equity.index, method='ffill')
                kospi = kospi / kospi.iloc[0] * 100
                plt.plot(kospi.index, kospi.values, label='KOSPI', alpha=0.7, linestyle='--')

            plt.title(f"Backtest: {args.strategy}")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig("data/backtest_equity_curve.png")
            print("Saved plot.")
    except Exception as e:
        print(f"Plot error: {e}")

    # Summary
    print("\n" + "="*50)
    print(f"SUMMARY ({args.strategy})")
    print(f"Stocks: {len(res_df)}")
    print(f"Avg Return: {res_df['return'].mean():.2f}%")
    print(f"Avg MDD: {res_df['mdd'].mean():.2f}%")
    print(f"Avg Win Rate: {res_df['win_rate'].mean():.2f}%")
    print("="*50)

    # Generate HTML Report
    try:
        from scripts.generate_html_report import generate_report
        generate_report(RESULT_FILE, TRADE_LOG_FILE)
    except Exception as e:
        print(f"Failed to generate HTML report: {e}")

if __name__ == "__main__":
    main()
