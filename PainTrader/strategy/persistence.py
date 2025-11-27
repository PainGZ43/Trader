import json
from datetime import datetime
from typing import Optional
from core.database import db
from strategy.base_strategy import StrategyState
from core.logger import get_logger

class StrategyStateDAO:
    """
    Data Access Object for Strategy State Persistence.
    Uses SQLite to store state.
    """
    def __init__(self):
        self.logger = get_logger("StrategyStateDAO")

    async def initialize(self):
        """
        Create table if not exists.
        """
        query = """
            CREATE TABLE IF NOT EXISTS strategy_state (
                strategy_id TEXT PRIMARY KEY,
                symbol TEXT,
                current_position INTEGER,
                avg_entry_price REAL,
                accumulated_profit REAL,
                indicators TEXT,
                last_update DATETIME
            )
        """
        await db.execute(query)

    async def save_state(self, state: StrategyState):
        """
        Save or Update strategy state.
        """
        query = """
            INSERT OR REPLACE INTO strategy_state 
            (strategy_id, symbol, current_position, avg_entry_price, accumulated_profit, indicators, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        indicators_json = json.dumps(state.indicators) if state.indicators else "{}"
        
        await db.execute(query, (
            state.strategy_id,
            state.symbol,
            state.current_position,
            state.avg_entry_price,
            state.accumulated_profit,
            indicators_json,
            state.last_update
        ))
        # self.logger.debug(f"Saved state for {state.strategy_id}")

    async def load_state(self, strategy_id: str) -> Optional[StrategyState]:
        """
        Load strategy state by ID.
        """
        query = "SELECT * FROM strategy_state WHERE strategy_id = ?"
        rows = await db.fetch_all(query, (strategy_id,))
        
        if not rows:
            return None
            
        row = rows[0]
        # row: (id, symbol, pos, avg, profit, indicators, last_update)
        
        try:
            indicators = json.loads(row[5])
        except:
            indicators = {}
            
        # Parse datetime if it's string (sqlite stores as string usually)
        last_update = row[6]
        if isinstance(last_update, str):
            try:
                last_update = datetime.fromisoformat(last_update)
            except:
                last_update = datetime.now() # Fallback

        return StrategyState(
            strategy_id=row[0],
            symbol=row[1],
            current_position=row[2],
            avg_entry_price=row[3],
            accumulated_profit=row[4],
            indicators=indicators,
            last_update=last_update
        )
