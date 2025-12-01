# Integration Testing & Deployment Plan

## Goal
Finalize the PainTrader AI application by performing comprehensive integration testing, handling edge cases, and packaging for distribution.

## User Review Required
> [!IMPORTANT]
> User needs to confirm the target environment for deployment (e.g., Windows 10/11, specific Python version requirements if not bundled).

## Detailed Tasks

### 1. Full Scenario Testing (End-to-End)
- **Objective**: Verify the complete trading lifecycle from login to shutdown under realistic conditions.
- **Scenarios**:
    - [ ] **Startup & Initialization**
        - Verify `ConfigLoader` loads correct environment (Real vs Mock).
        - Confirm `SecureStorage` unlocks API keys.
        - Check `KiwoomRestClient` login and token refresh.
        - Validate `WebSocketClient` connection and subscription to target symbols.
    - [ ] **Strategy Execution**
        - **Signal Generation**: Feed historical data to `HybridStrategy` and verify `BUY`/`SELL` signals.
        - **Order Creation**: Confirm `OrderManager` converts signals to valid orders (price, qty checks).
    - [ ] **Order Lifecycle**
        - **Submission**: Send order to `PaperExchange` (or Real API in test mode).
        - **Fill Simulation**: Verify partial fills and full fills update `AccountManager`.
        - **Cancellation**: Test `cancel_order` and `cancel_all` functionality.
    - [ ] **Risk Management**
        - **Stop Loss**: Simulate price drop to trigger stop-loss logic.
        - **Position Limit**: Try to open positions exceeding `max_position_pct`.
    - [ ] **Shutdown & Persistence**
        - Verify open orders are cancelled (if configured).
        - Check `trade.db` for saved trade history.
        - Confirm application exits cleanly without zombie processes.

### 2. Exception Handling & Resilience
- **Objective**: Ensure the application is robust against external failures.
- **Tests**:
    - [ ] **Network Disconnection**
        - Action: Disable network adapter while running.
        - Expected: `WebSocketClient` detects disconnect -> Retries -> Reconnects when network restored.
    - [ ] **API Rate Limiting**
        - Action: Force rapid API calls exceeding limit.
        - Expected: `RateLimiter` blocks calls or API returns 429 -> Application waits/retries.
    - [ ] **Data Anomalies**
        - Action: Inject malformed JSON or zero price data.
        - Expected: `DataCollector` logs warning and discards data (no crash).
    - [ ] **Critical Failure (Panic)**
        - Action: Click "Panic Button" (Stop Algo / Liquidate).
        - Expected: All active orders cancelled, positions closed (if Liquidate), Algo stops.

### 3. Packaging & Distribution
- **Objective**: Create a robust standalone executable (`.exe`).
- **Tools**: `PyInstaller`
- **Critical Technical Considerations**:
    - **Path Handling (Verified)**:
        - **Issue**: `Program Files` is read-only. Relative paths (`logs/`, `trade.db`) will fail.
        - **Solution**: Implement `get_user_data_dir()` utility.
            - **Logs**: `%APPDATA%/PainTrader/logs`
            - **DB**: `%APPDATA%/PainTrader/trade.db`
            - **Config**: `%APPDATA%/PainTrader/settings.json` (Copy template if missing)
        - **Implementation**: Modify `core/config.py` and `core/logger.py` to use this utility.
    - **Console Safety**:
        - **Issue**: In `--noconsole` mode, `sys.stdout` might be `None`.
        - **Solution**: Modify `core/logger.py` to check `if sys.stdout:` before adding `StreamHandler`.
    - **Architecture**:
        - **Confirmed**: Pure REST API used. **No 32-bit restriction**. **No OCX dependency**.
        - **Target**: 64-bit Windows.
- **Configuration (`PainTrader.spec`)**:
    - **Entry Point**: `main.py`
    - **Hidden Imports**: 
        - `pandas`, `numpy`, `ta-lib`
        - `PyQt6.QtCore`, `PyQt6.QtGui`, `PyQt6.QtWidgets`
        - `sqlite3`, `keyring.backends.Windows`
        - `aiohttp`, `asyncio`
    - **Data Files**:
        - `ui/resources/` -> `ui/resources/`
        - `ui/styles.qss` -> `ui/styles.qss`
        - `config/settings.json` (Template) -> `config/settings.json`
    - **Icon**: `ui/resources/icon.ico`
- **Steps**:
    1. **Code Refactoring**: 
        - Create `core/utils.py` with `get_user_data_dir()`.
        - Update `Logger` and `ConfigLoader` to use it.
        - Safe-guard `sys.stdout` usage.
    2. **Spec Generation**: `pyi-makespec --onefile --windowed --name PainTrader --icon=ui/resources/icon.ico main.py`
    3. **Build**: `pyinstaller PainTrader.spec`
    4. **Verification**: Test on a clean VM (Mock Mode first, then Real).

### 4. Documentation
- **Artifacts**:
    - `README.md`: Installation, Configuration, Usage.
    - `USER_MANUAL.md`: Detailed guide for UI features (Dashboard, Settings, Panic Button).
    - `TROUBLESHOOTING.md`: Common errors (API login, Network) and fixes.

## Verification Plan
### Automated Tests
- `verify_integration.py`: Existing script for core event flow.
- `verify_recovery.py`: New script to simulate component failures (mocking).

### Manual Verification Checklist
- [ ] Launch `.exe` without Python installed.
- [ ] Connect to Kiwoom API (Mock/Real).
- [ ] Execute 1 Buy and 1 Sell order.
- [ ] Change Language (KO -> EN) and Restart.
- [ ] Verify Log file creation and rotation.
