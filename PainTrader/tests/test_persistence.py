import pytest
import asyncio
import os
from datetime import datetime
from strategy.persistence import StrategyStateDAO
from strategy.base_strategy import StrategyState
from core.database import Database

@pytest.mark.asyncio
async def test_persistence_flow(tmp_path):
    # 1. Setup Temp DB
    db_path = tmp_path / "test_trade.db"
    
    # Handle Singleton: Get instance and override path
    test_db = Database()
    # Force re-initialization for test
    test_db.db_path = str(db_path)
    if test_db.conn:
        await test_db.close()
    await test_db.connect()
    
    # Patch the global db in persistence module
    with pytest.MonkeyPatch.context() as m:
        m.setattr("strategy.persistence.db", test_db)
        
        dao = StrategyStateDAO()
        await dao.initialize()
        
        test_id = "test_strategy_persist_1"
        state = StrategyState(
            strategy_id=test_id,
            symbol="005930",
            current_position=10,
            avg_entry_price=50000.0,
            accumulated_profit=1000.0,
            indicators={"RSI": 30.5},
            last_update=datetime.now()
        )
        
        # 2. Save
        await dao.save_state(state)
        
        # 3. Load
        loaded_state = await dao.load_state(test_id)
        
        # 4. Verify
        assert loaded_state is not None
        assert loaded_state.strategy_id == test_id
        assert loaded_state.current_position == 10
        assert loaded_state.avg_entry_price == 50000.0
        assert loaded_state.indicators["RSI"] == 30.5
        
        # 5. Update
        state.current_position = 0
        state.accumulated_profit = 2000.0
        await dao.save_state(state)
        
        loaded_state_updated = await dao.load_state(test_id)
        assert loaded_state_updated.current_position == 0
        assert loaded_state_updated.accumulated_profit == 2000.0
        
    await test_db.close()
