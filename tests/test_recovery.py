import pytest
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from unittest.mock import MagicMock, AsyncMock
from execution.engine import ExecutionEngine
from execution.order_manager import OrderManager
from strategy.base_strategy import BaseStrategy, StrategyState
from strategy.persistence import StrategyStateDAO
from core.database import db
from core.event_bus import event_bus

class MockStrategy(BaseStrategy):
    def __init__(self, strategy_id, symbol):
        super().__init__(strategy_id, symbol)
        
    async def on_realtime_data(self, data):
        return None
        
    def calculate_signals(self, df):
        return df

@pytest.mark.asyncio
async def test_strategy_state_persistence():
    # Setup DB
    db.db_path = ":memory:"
    await db.connect()
    await db.execute("CREATE TABLE IF NOT EXISTS strategy_state (strategy_id TEXT PRIMARY KEY, symbol TEXT, current_position INTEGER, avg_entry_price REAL, accumulated_profit REAL, indicators TEXT, last_update DATETIME)")
    
    dao = StrategyStateDAO()
    
    # 1. Save State
    strategy_id = "TEST_STRATEGY"
    initial_state = StrategyState(
        strategy_id=strategy_id, 
        symbol="005930", 
        current_position=10, 
        avg_entry_price=50000, 
        accumulated_profit=1000
    )
    
    await dao.save_state(initial_state)
    
    # 2. Initialize Engine & Restore
    kiwoom_mock = MagicMock()
    engine = ExecutionEngine(kiwoom_mock, mode="PAPER")
    engine.strategy_dao = dao 
    
    strategy = MockStrategy(strategy_id, "005930")
    engine.register_strategy(strategy)
    
    # Manually trigger restore since register_strategy is sync and doesn't do it anymore
    await engine.restore_strategies_state()
    
    # 3. Verify
    restored_state = strategy.get_state()
    assert restored_state.current_position == 10
    assert restored_state.avg_entry_price == 50000
    assert restored_state.accumulated_profit == 1000
    
    await db.close()

@pytest.mark.asyncio
async def test_order_filled_updates_state():
    # Setup DB
    db.db_path = ":memory:"
    await db.connect()
    await db.execute("CREATE TABLE IF NOT EXISTS strategy_state (strategy_id TEXT PRIMARY KEY, symbol TEXT, current_position INTEGER, avg_entry_price REAL, accumulated_profit REAL, indicators TEXT, last_update DATETIME)")
    
    kiwoom_mock = MagicMock()
    engine = ExecutionEngine(kiwoom_mock, mode="PAPER")
    await engine.initialize() # Subscribes to event
    
    strategy_id = "TEST_STRATEGY_2"
    strategy = MockStrategy(strategy_id, "005930")
    engine.register_strategy(strategy)
    
    # 1. Emit Order Filled Event
    event_data = {
        "order_id": "ORD123",
        "symbol": "005930",
        "type": "BUY",
        "price": 60000,
        "qty": 5,
        "strategy_id": strategy_id
    }
    
    class MockEvent:
        def __init__(self, data):
            self.data = data
            
    engine._on_order_filled(MockEvent(event_data))
    
    # Wait for async save to complete
    await asyncio.sleep(0.1)
    
    # 2. Verify Strategy State Updated
    current_state = strategy.get_state()
    assert current_state.current_position == 5
    assert current_state.avg_entry_price == 60000
    
    # 3. Verify DB Saved
    dao = StrategyStateDAO()
    saved_state = await dao.load_state(strategy_id)
    assert saved_state.current_position == 5
    assert saved_state.avg_entry_price == 60000
    
    await db.close()

from datetime import datetime

@pytest.mark.asyncio
async def test_order_manager_emits_event():
    # Setup
    kiwoom_mock = MagicMock()
    order_manager = OrderManager(kiwoom_mock)
    # Mock DB for OrderManager
    db.db_path = ":memory:"
    await db.connect()
    await order_manager.initialize()
    
    # Mock EventBus
    mock_callback = MagicMock()
    event_bus.subscribe("order.filled", mock_callback)
    
    # Simulate Order Fill
    order_id = "ORD999"
    order_manager.active_orders[order_id] = {
        'symbol': "005930",
        'type': "BUY",
        'quantity': 10,
        'filled_qty': 0,
        'price': 50000,
        'source': 'STRATEGY',
        'timestamp': datetime.now(),
        'strategy_id': "TEST_STRATEGY"
    }
    
    event_data = {
        'order_no': order_id,
        'status': 'FILLED',
        'exec_qty': 5,
        'qty': 5,
        'price': 50000
    }
    
    await order_manager.on_order_event(event_data)
    
    # Wait for EventBus to dispatch
    await asyncio.sleep(0.1)
    
    # Verify Event Emitted
    assert mock_callback.called
    args, _ = mock_callback.call_args
    event_obj = args[0]
    event_payload = event_obj.data
    assert event_payload['order_id'] == order_id
    assert event_payload['qty'] == 5
    assert event_payload['strategy_id'] == "TEST_STRATEGY"
    
    await db.close()
