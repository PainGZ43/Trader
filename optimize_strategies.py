import asyncio
import pandas as pd
import numpy as np
import itertools
from strategy.built_in_strategies import VolatilityBreakoutStrategy, SimpleMAStrategy, RSIStrategy, BollingerBandStrategy, MACDStrategy

def generate_mock_data(days=100):
    """Generate mock OHLCV data for testing."""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
    data = {
        'open': np.random.uniform(100, 200, days),
        'high': np.random.uniform(100, 200, days),
        'low': np.random.uniform(100, 200, days),
        'close': np.random.uniform(100, 200, days),
        'volume': np.random.uniform(1000, 10000, days)
    }
    # Ensure High is highest and Low is lowest
    df = pd.DataFrame(data, index=dates)
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    return df

class StrategyOptimizer:
    def __init__(self):
        self.strategies = {
            "VolBreakout": VolatilityBreakoutStrategy,
            "SimpleMA": SimpleMAStrategy,
            "RSI": RSIStrategy,
            "Bollinger": BollingerBandStrategy,
            "MACD": MACDStrategy
        }

    def backtest(self, strategy_class, config, df):
        """Simple backtest simulation."""
        strategy = strategy_class(name="Test", config=config)
        signals = []
        
        # Simulate day by day (simplified)
        # For indicators, we need enough history.
        # We'll just run calculate_signals on the full DF for simplicity in this mock optimizer
        # In real backtest, we'd iterate.
        
        # Note: VolBreakout needs daily iteration for target calculation.
        # Others can calculate on full DF.
        
        balance = 1000000
        position = 0
        buy_price = 0
        trades = 0
        wins = 0
        
        # Iterating to simulate real-time
        for i in range(50, len(df)):
            current_slice = df.iloc[:i+1]
            current_price = current_slice.iloc[-1]['close']
            
            signal = None
            
            if isinstance(strategy, VolatilityBreakoutStrategy):
                strategy.calculate_target(current_slice)
                # Mocking realtime check: if High > Target
                if strategy.target_price and current_slice.iloc[-1]['high'] > strategy.target_price:
                    # Buy at Target Price
                    signal = "BUY"
                    current_price = strategy.target_price # Fill at target
            else:
                signal = strategy.calculate_signals(current_slice)
            
            if signal == "BUY" and position == 0:
                position = 1
                buy_price = current_price
                trades += 1
            elif (signal == "SELL" or (isinstance(strategy, VolatilityBreakoutStrategy) and position == 1)) and position == 1:
                # VolBreakout sells at close (simplified)
                position = 0
                profit = (current_price - buy_price) / buy_price
                balance *= (1 + profit)
                if profit > 0:
                    wins += 1
                    
        return {
            "return": (balance - 1000000) / 1000000 * 100,
            "trades": trades,
            "win_rate": (wins / trades * 100) if trades > 0 else 0
        }

    def grid_search(self, strategy_name, param_grid, df):
        print(f"Optimizing {strategy_name}...")
        strategy_class = self.strategies.get(strategy_name)
        if not strategy_class:
            print(f"Strategy {strategy_name} not found.")
            return

        keys, values = zip(*param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        results = []
        for config in combinations:
            res = self.backtest(strategy_class, config, df)
            res.update(config)
            results.append(res)
            
        # Sort by Return
        results.sort(key=lambda x: x['return'], reverse=True)
        
        print(f"--- Top 3 Configurations for {strategy_name} ---")
        for i in range(min(3, len(results))):
            print(f"Rank {i+1}: {results[i]}")
        print("\n")

def main():
    optimizer = StrategyOptimizer()
    df = generate_mock_data(200)
    
    # 1. Volatility Breakout
    optimizer.grid_search("VolBreakout", {
        "k": [0.4, 0.5, 0.6, 0.7]
    }, df)
    
    # 2. Simple MA
    optimizer.grid_search("SimpleMA", {
        "short_window": [3, 5, 10],
        "long_window": [10, 20, 60]
    }, df)
    
    # 3. RSI
    optimizer.grid_search("RSI", {
        "period": [9, 14, 25],
        "buy_threshold": [20, 30, 40],
        "sell_threshold": [60, 70, 80]
    }, df)
    
    # 4. Bollinger
    optimizer.grid_search("Bollinger", {
        "period": [20],
        "std_dev": [1.5, 2.0, 2.5]
    }, df)
    
    # 5. MACD
    optimizer.grid_search("MACD", {
        "fast": [12, 5],
        "slow": [26, 34],
        "signal": [9, 5]
    }, df)

if __name__ == "__main__":
    main()
