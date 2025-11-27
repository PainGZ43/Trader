import pandas as pd
import numpy as np
from typing import Dict, Any, List
from strategy.base_strategy import StrategyInterface, Signal
from strategy.position_sizer import PositionSizer
from core.logger import get_logger

class BacktestResult:
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        self.final_capital = 0.0
        self.total_return = 0.0
        self.mdd = 0.0
        self.win_rate = 0.0

class EventDrivenBacktester:
    """
    Event-Driven Backtester.
    Simulates trading by iterating through historical data as if it were real-time.
    """
    def __init__(self):
        self.logger = get_logger("Backtester")
        self.initial_capital = 10_000_000
        self.commission_rate = 0.00015 # 0.015%
        self.slippage_rate = 0.0005 # 0.05% (Approx 1 tick for 20000 KRW stock)
        self.use_tick_data = False # Default to 1m bars

    def configure(self, config: Dict[str, Any]):
        self.initial_capital = config.get("initial_capital", 10_000_000)
        self.commission_rate = config.get("commission_rate", 0.00015)
        self.slippage_rate = config.get("slippage_rate", 0.0005)
        self.use_tick_data = config.get("use_tick_data", False)

    def run(self, strategy: StrategyInterface, data: pd.DataFrame) -> BacktestResult:
        """
        Run backtest.
        data: OHLCV DataFrame
        """
        self.logger.info(f"Starting Backtest for {strategy.__class__.__name__}...")
        
        capital = self.initial_capital
        position = 0
        avg_price = 0.0
        equity_curve = []
        trades = []
        
        # Pre-calculate signals if strategy supports batch calculation (Hybrid/Vectorized)
        # However, for true event-driven, we should call on_realtime_data row by row.
        # But calling on_realtime_data for every row is slow in Python.
        # Hybrid approach: Calculate signals vectorized, then simulate execution event-driven.
        
        # 1. Calculate Signals Vectorized
        df_signals = strategy.calculate_signals(data)
        
        # 2. Iterate and Simulate Execution
        for index, row in df_signals.iterrows():
            current_price = row['close']
            signal = row.get('signal', 0)
            
            # Equity Calculation (Mark to Market)
            equity = capital
            if position != 0:
                equity += (current_price - avg_price) * position
            equity_curve.append(equity)
            
            # Execution Logic
            if signal == 1 and position == 0: # Buy Signal & No Position
                # Calculate Size
                # For simplicity in backtest, use fixed fractional or simple logic if position_sizer not injected
                # Assuming strategy has position_sizer or we use default
                # Let's use a simple logic: Buy max possible
                buy_price = current_price * (1 + self.slippage_rate)
                max_shares = int(capital / buy_price)
                
                if max_shares > 0:
                    cost = max_shares * buy_price
                    fee = cost * self.commission_rate
                    capital -= (cost + fee)
                    position = max_shares
                    avg_price = buy_price
                    trades.append({"type": "BUY", "price": buy_price, "qty": max_shares, "time": index})
                    
            elif signal == -1 and position > 0: # Sell Signal & Has Position
                sell_price = current_price * (1 - self.slippage_rate)
                revenue = position * sell_price
                fee = revenue * self.commission_rate
                capital += (revenue - fee)
                
                # Record Trade
                profit = (sell_price - avg_price) * position
                trades.append({"type": "SELL", "price": sell_price, "qty": position, "time": index, "profit": profit})
                
                position = 0
                avg_price = 0.0

        # Finalize
        final_equity = equity_curve[-1] if equity_curve else self.initial_capital
        
        result = BacktestResult()
        result.trades = trades
        result.equity_curve = equity_curve
        result.final_capital = final_equity
        result.total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Calculate MDD
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        result.mdd = drawdown.min() * 100 if not drawdown.empty else 0.0
        
        # Win Rate
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        result.win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0.0
        
        self.logger.info(f"Backtest Finished. Return: {result.total_return:.2f}%, MDD: {result.mdd:.2f}%")
        return result
