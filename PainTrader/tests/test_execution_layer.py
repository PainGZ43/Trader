import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from execution.risk_manager import RiskManager
from execution.order_manager import OrderManager
from execution.engine import ExecutionEngine
from strategy.base_strategy import Signal
from data.kiwoom_rest_client import KiwoomRestClient

@pytest.fixture
def mock_kiwoom():
    kiwoom = MagicMock(spec=KiwoomRestClient)
    kiwoom.send_order = AsyncMock(return_value={"result_code": 0})
    return kiwoom

def test_risk_manager():
    rm = RiskManager()
    rm.configure({"max_daily_loss_rate": 0.03, "max_order_count_per_min": 2})
    
    signal = Signal("005930", "BUY", 60000, datetime.now(), "Test")
    account_info = {"daily_pnl": -400000, "total_asset": 10000000, "deposit": 5000000} # -4% Loss
    
    # 1. Daily Loss Check (Should Fail)
    assert rm.check_risk(signal, account_info) == False
    
    # 2. Daily Loss Check (Should Pass for SELL)
    signal.type = "SELL"
    assert rm.check_risk(signal, account_info) == True
    
    # 3. Order Count Check
    signal.type = "BUY"
    account_info["daily_pnl"] = 0 # Reset Loss
    
    # Count = 0
    assert rm.check_risk(signal, account_info) == True
    rm.record_order()
    
    # Count = 1
    assert rm.check_risk(signal, account_info) == True
    rm.record_order()
    
    # Count = 2 (Limit Reached)
    assert rm.check_risk(signal, account_info) == False

@pytest.mark.asyncio
async def test_execution_engine(mock_kiwoom):
    engine = ExecutionEngine(mock_kiwoom, mode="REAL")
    # Inject Mock Kiwoom (Redundant but safe)
    engine.kiwoom = mock_kiwoom
    engine.exchange = mock_kiwoom
    engine.order_manager.kiwoom = mock_kiwoom
    
    # Mock AccountManager to avoid real sync
    engine.account_manager = MagicMock()
    engine.account_manager.get_summary.return_value = {
        "balance": {"deposit": 10000000, "total_asset": 10000000, "daily_pnl": 0},
        "positions": {}
    }
    # Mock check_buying_power
    engine.account_manager.check_buying_power.return_value = True
    
    # Initialize (Skip real init)
    # await engine.initialize() # We mocked AM, so no need to sync
    
    signal = Signal("005930", "BUY", 60000, datetime.now(), "Test")
    
    # Execute
    await engine.execute_signal(signal, 10)
    
    # Verify Kiwoom called
    mock_kiwoom.send_order.assert_called_once()
    args = mock_kiwoom.send_order.call_args[0]
    # args: (symbol, order_type, qty, price, trade_type)
    assert args[0] == "005930"
    assert args[2] == 10
    assert args[3] == 60000
