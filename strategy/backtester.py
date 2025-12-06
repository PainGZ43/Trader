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
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0
        self.max_drawdown_duration = 0

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
        self.latency_ticks = 1
        self.impact_cost_factor = 0.0001

    def configure(self, config: Dict[str, Any]):
        self.initial_capital = config.get("initial_capital", 10_000_000)
        self.commission_rate = config.get("commission_rate", 0.00015)
        self.slippage_rate = config.get("slippage_rate", 0.0005)
        self.use_tick_data = config.get("use_tick_data", False)
        # Refinement: Latency & Market Impact
        self.latency_ticks = config.get("latency_ticks", 1) # Delay in candles/ticks
        self.impact_cost_factor = config.get("impact_cost_factor", 0.0001) # Impact per 1% of volume

    def run(self, strategy: StrategyInterface, data: pd.DataFrame) -> BacktestResult:
        """
        Run backtest.
        data: OHLCV DataFrame
        """
        # self.logger.info(f"Starting Backtest for {strategy.__class__.__name__}...")
        
        capital = self.initial_capital
        position = 0
        avg_price = 0.0
        equity_curve = []
        trades = []
        
        # 1. Calculate Signals Vectorized
        df_signals = strategy.calculate_signals(data)
        
        # Queue for delayed orders (Latency Simulation)
        # Format: (execute_at_index, signal, price_at_signal)
        order_queue = [] 
        
        # 2. Iterate and Simulate Execution
        # We need integer index for queue handling
        for i in range(len(df_signals)):
            row = df_signals.iloc[i]
            current_price = row['close']
            current_volume = row['volume']
            signal = row.get('signal', 0)
            
            # Skip invalid data
            if current_price <= 0:
                equity_curve.append(equity)
                continue
            
            # Equity Calculation (Mark to Market)
            equity = capital
            if position != 0:
                equity += current_price * position
            equity_curve.append(equity)
            
            # 1. Process Delayed Orders
            if order_queue and order_queue[0][0] <= i:
                _, pending_signal, _ = order_queue.pop(0)
                
                # Execute Logic (Same as before but with dynamic slippage)
                if pending_signal == 1 and position == 0: # Buy
                    # Dynamic Slippage: Base + Impact
                    # Impact: If we buy 1% of volume, price moves impact_cost_factor
                    # Estimate size first
                    est_price = current_price * (1 + self.slippage_rate)
                    # Use 95% of capital to leave room for impact cost and fees
                    max_shares = int((capital * 0.95) / est_price)
                    
                    if max_shares > 0 and current_volume > 0:
                        volume_share = max_shares / current_volume
                        impact = volume_share * self.impact_cost_factor
                        real_slippage = self.slippage_rate + impact
                        
                        buy_price = current_price * (1 + real_slippage)
                        cost = max_shares * buy_price
                        fee = cost * self.commission_rate
                        
                        if capital >= cost + fee:
                            capital -= (cost + fee)
                            position = max_shares
                            avg_price = buy_price
                            trades.append({"type": "BUY", "price": buy_price, "qty": max_shares, "time": df_signals.index[i]})
                            
                elif pending_signal == -1 and position > 0: # Sell
                    volume_share = position / current_volume if current_volume > 0 else 0
                    impact = volume_share * self.impact_cost_factor
                    real_slippage = self.slippage_rate + impact
                    
                    sell_price = current_price * (1 - real_slippage)
                    revenue = position * sell_price
                    fee = revenue * self.commission_rate
                    capital += (revenue - fee)
                    
                    profit = (sell_price - avg_price) * position
                    trades.append({"type": "SELL", "price": sell_price, "qty": position, "time": df_signals.index[i], "profit": profit})
                    
                    position = 0
                    avg_price = 0.0

            # 2. Handle New Signals (Add to Queue)
            if signal != 0:
                execute_at = i + self.latency_ticks
                if execute_at < len(df_signals):
                    order_queue.append((execute_at, signal, current_price))
                else:
                    pass # Signal too late, ignore or execute at end? Ignore for now.

        # Finalize
        final_equity = equity_curve[-1] if equity_curve else self.initial_capital
        
        result = BacktestResult()
        result.trades = trades
        result.equity_curve = equity_curve
        result.final_capital = final_equity
        result.total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Calculate MDD & Duration
        equity_series = pd.Series(equity_curve, index=df_signals.index)
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        result.mdd = drawdown.min() * 100 if not drawdown.empty else 0.0
        
        # MDD Duration (Longest time in drawdown)
        if not drawdown.empty:
            is_drawdown = drawdown < 0
            # Group consecutive True values
            # This is a bit complex in pandas, simplified approach:
            # Count consecutive days where drawdown < 0
            # Or just find the max duration between peaks
            # Let's use a simpler approximation: Max days between new highs
            high_indices = equity_series[equity_series == rolling_max].index
            if len(high_indices) > 1:
                durations = pd.Series(high_indices).diff().dt.days
                result.max_drawdown_duration = durations.max()
            else:
                result.max_drawdown_duration = (equity_series.index[-1] - equity_series.index[0]).days

        # Win Rate
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        result.win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0.0
        
        # Sharpe & Sortino Ratio
        # Calculate daily returns
        if not equity_series.empty:
            # Resample to daily if data is intraday, or just use pct_change if daily
            # Assuming daily data for now or taking pct_change of equity curve directly
            # If intraday, this might be noisy. Let's resample to daily.
            daily_equity = equity_series.resample('D').last().dropna()
            if len(daily_equity) > 1:
                daily_returns = daily_equity.pct_change().dropna()
                
                # Annualize factor (Crypto 365, Stock 252) -> Assuming Stock 252
                annual_factor = np.sqrt(252)
                
                mean_return = daily_returns.mean()
                std_return = daily_returns.std()
                
                if std_return != 0:
                    result.sharpe_ratio = (mean_return / std_return) * annual_factor
                
                # Sortino (Downside deviation)
                downside_returns = daily_returns[daily_returns < 0]
                downside_std = downside_returns.std()
                
                if downside_std != 0:
                    result.sortino_ratio = (mean_return / downside_std) * annual_factor

        # self.logger.info(f"Backtest Finished. Return: {result.total_return:.2f}%, MDD: {result.mdd:.2f}%")
        return result
