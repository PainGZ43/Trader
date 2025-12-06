# PainTrader Backtest Guide

This document provides a guide on backtesting scenarios and the step-by-step process to use the **Backtest Lab**.

## 1. Backtest Scenarios

Here are some common trading scenarios you can test with the built-in strategies:

### Scenario A: Trend Following (Volatility Breakout)
*   **Hypothesis**: If the price breaks above a certain range from the open, it indicates strong momentum that will continue for the day.
*   **Strategy**: `VolatilityBreakoutStrategy`
*   **Key Parameter**: `k` (Range Multiplier).
    *   `k = 0.5`: Standard setting.
    *   `k < 0.5`: More aggressive entry (more trades, potentially more false signals).
    *   `k > 0.5`: More conservative entry.
*   **Target Market**: High volatility stocks or trending markets.

### Scenario B: Trend Following (Moving Average Crossover)
*   **Hypothesis**: When a short-term moving average crosses above a long-term moving average, an uptrend is starting.
*   **Strategy**: `MovingAverageCrossoverStrategy`
*   **Key Parameters**:
    *   `short_window` (e.g., 5, 10, 20)
    *   `long_window` (e.g., 20, 60, 120)
*   **Target Market**: Stable trending stocks (e.g., Samsung Electronics during a bull run).

### Scenario C: Mean Reversion (RSI)
*   **Hypothesis**: Assets that are "oversold" will bounce back, and "overbought" assets will pull back.
*   **Strategy**: `RSIStrategy`
*   **Key Parameters**:
    *   `buy_threshold` (e.g., 30): Buy when RSI drops below this.
    *   `sell_threshold` (e.g., 70): Sell when RSI rises above this.
*   **Target Market**: Range-bound or sideways markets.

## 2. Backtest Process (How to Use)

The **Backtest Lab** allows you to simulate these scenarios without writing code.

### Step 1: Open Backtest Lab
1.  Launch **PainTrader**.
2.  Click the **Flask Icon (Backtest)** button in the top header bar.

### Step 2: Configure Simulation
1.  **Strategy**: Select the strategy you want to test (e.g., `VolatilityBreakoutStrategy`).
2.  **Symbol**: Search for a stock (e.g., type "Samsung" or "005930").
3.  **Date Range**:
    *   **Start**: Select the beginning of the historical data period.
    *   **End**: Select the end date.
    *   *Note*: Ensure the range is long enough to generate signals (at least a few months recommended).

### Step 3: Run Simulation
1.  Click the **"Run Backtest"** button.
2.  The system will:
    *   Fetch historical OHLCV data for the selected period.
    *   Initialize the strategy.
    *   Replay the market data day-by-day (or minute-by-minute if available).
    *   Simulate trades including fees (0.015%) and slippage (0.05%).

### Step 4: Analyze Results
1.  **Equity Curve**: Look at the blue line chart.
    *   Is it generally going up?
    *   Are there steep drops (drawdowns)?
2.  **Metrics Table**:
    *   **Total Return**: Did you make money?
    *   **MDD (Max Drawdown)**: What was the worst peak-to-valley loss? (Lower is better).
    *   **Win Rate**: How often did you win?
3.  **Trade List**: Review individual trades to see *why* the strategy bought or sold at specific times.

## 3. Tips for Better Backtesting
*   **Test Multiple Periods**: Don't just test a bull market. Test a bear market (e.g., 2022) to see if your strategy survives.
*   **Watch Out for Overfitting**: Tuning parameters (like `k=0.43`) to perfectly match past data often fails in the future. Stick to robust, round numbers.
*   **Consider Liquidity**: The backtester assumes you can always buy/sell at the close price. In reality, low volume stocks might have higher slippage.
