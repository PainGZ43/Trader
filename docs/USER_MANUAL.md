# PainTrader User Manual

## 1. Introduction
**PainTrader** is an advanced AI-powered automated trading system designed for the Korean stock market (Kiwoom Securities). It combines real-time data analysis, technical indicators, and AI models to execute trades automatically.

## 2. Installation & Setup

### Prerequisites
- **OS**: Windows 10 or 11 (64-bit recommended)
- **Kiwoom Open API**: Must be installed and logged in at least once.
- **KOA Studio**: Recommended for testing API connectivity.

### Running the Application
1. Locate the `PainTrader.exe` file in the distribution folder.
2. Double-click to launch.
3. Ensure Kiwoom Open API login window appears (if not auto-logged in).

### API Key Setup
1. On first launch, if no API keys are detected, you will be prompted to open Settings.
2. Go to **Settings > Account**.
3. Enter your Kiwoom Account ID and other required details.
4. Click **Save**.

## 3. Dashboard Overview

The main window is divided into several sections:

### Header Bar
- Displays current market status (Open/Closed).
- Shows KOSPI/USD indices.
- Quick access to Settings and Logs.

### Dashboard (Center)
- **Real-time Chart**: Displays candlestick chart with moving averages.
- **Order Book**: Shows real-time ask/bid prices and volumes.

### Control Panel (Left)
- **Account Summary**: Total Asset, Deposit, PnL, and Returns.
- **Portfolio**: List of currently held positions with real-time PnL.
- **Close Position**: Click the 'X' button to manually liquidate a position.

### Order Panel (Right)
- **Manual Order**: Buy/Sell stocks manually.
- **Quick Qty**: Buttons to quickly set quantity based on % of deposit.
- **Panic Button**:
    - **Stop Algo**: Pauses all automated trading.
    - **Cancel All**: Cancels all active non-filled orders.
    - **Liquidate**: Sells all holdings immediately (requires confirmation).

### Log Viewer (Bottom)
- Displays system logs, trade execution history, and error messages.

## 4. Configuration

### Strategy Settings
- Go to **Settings > Strategy**.
- Select active strategies (e.g., Volatility Breakout, RSI, AI Hybrid).
- Adjust parameters like `target_profit`, `stop_loss`, etc.

### Risk Management
- Go to **Settings > Risk**.
- Set **Max Loss Limit**: Daily loss limit to stop trading.
- Set **Max Position Size**: Maximum % of capital per stock.

### Notifications
- Go to **Settings > Notification**.
- Enable **KakaoTalk** notifications.
- Enter your KakaoTalk Access Token (refer to developer guide for token generation).

## 5. Troubleshooting

### "Waiting for data..." in Order Book
- Ensure the market is open.
- Check if Kiwoom API is connected (System Monitor in Settings).

### Application Crashes on Start
- Check `logs/` directory for error files.
- Ensure Python 32-bit/64-bit compatibility if running from source.

### Orders Not Executing
- Check **Risk Limits** in Settings.
- Verify **Deposit** is sufficient.
- Check if **Panic Mode** (Stop Algo) is active.
