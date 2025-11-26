import pytest
import pytest_asyncio
import asyncio
import os
import aiosqlite
from unittest.mock import patch
from core.database import Database
from core.config import config

@pytest_asyncio.fixture
async def test_db():
    # Use a temp db file
    db_path = "tests/test_trade.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Patch config to use temp db
    original_path = config.get("DB_PATH")
    config._config["DB_PATH"] = db_path
    
    # Reset singleton
    Database._instance = None
    db = Database()
    await db.connect()
    
    yield db
    
    await db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Restore config
    if original_path:
        config._config["DB_PATH"] = original_path

@pytest.mark.asyncio
async def test_database_connection(test_db):
    """Test database connection and table creation."""
    assert test_db.conn is not None
    
    # Check tables exist
    tables = await test_db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    assert "market_data" in table_names
    assert "trade_history" in table_names
    assert "strategy_state" in table_names

@pytest.mark.asyncio
async def test_database_crud(test_db):
    """Test Insert and Select operations."""
    # Insert
    await test_db.execute(
        "INSERT INTO market_data (timestamp, symbol, interval, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('2023-01-01 09:00:00', '005930', '1m', 100, 110, 90, 105, 1000)
    )
    
    # Select
    rows = await test_db.fetch_all("SELECT * FROM market_data WHERE symbol='005930'")
    assert len(rows) == 1
    assert rows[0]['close'] == 105

@pytest.mark.asyncio
async def test_database_persistence(test_db):
    """Test Strategy State Persistence."""
    state = '{"position": "long"}'
    await test_db.execute(
        "INSERT OR REPLACE INTO strategy_state (symbol, state_json) VALUES (?, ?)",
        ('005930', state)
    )
    
    rows = await test_db.fetch_all("SELECT state_json FROM strategy_state WHERE symbol='005930'")
    assert rows[0]['state_json'] == state

@pytest.mark.asyncio
async def test_database_connection_error():
    """Test connection failure."""
    from unittest.mock import patch
    
    Database._instance = None
    db = Database()
    
    with patch('aiosqlite.connect', side_effect=Exception("Connection Failed")):
        with pytest.raises(Exception):
            await db.connect()

@pytest.mark.asyncio
async def test_database_query_error(test_db):
    """Test query execution failure."""
    # Mock execute to raise exception
    # We need to patch the connection object's execute method
    # Since test_db fixture already connected, we can patch test_db.conn.execute
    
    # Note: aiosqlite.Connection.execute is an async context manager
    # So we need to mock it carefully if we want to simulate failure inside it or during it
    # But Database.execute calls await self.conn.execute(...)
    
    # Easiest way is to pass invalid SQL
    with pytest.raises(Exception):
        await test_db.execute("INVALID SQL")
        
    with pytest.raises(Exception):
        await test_db.fetch_all("INVALID SQL")

@pytest.mark.asyncio
async def test_database_auto_connect():
    """Test auto-connect on execute/fetch."""
    Database._instance = None
    db = Database()
    # Don't call connect()
    
    # We need to mock connect to avoid real DB file creation if possible, 
    # or just let it connect to default 'trade.db' (or patched path)
    
    # Let's patch connect to verify it's called
    with patch.object(db, 'connect', side_effect=db.connect) as mock_connect:
        # We need to actually let it connect to work, so side_effect calls original
        # But we need to ensure db_path is safe
        db.db_path = "tests/test_auto_connect.db"
        
        try:
            await db.execute("CREATE TABLE IF NOT EXISTS test (id INT)")
            mock_connect.assert_called()
            
            # Test fetch_all auto-connect
            await db.fetch_all("SELECT 1")
            assert mock_connect.call_count >= 1
        finally:
            await db.close()
            if os.path.exists(db.db_path):
                os.remove(db.db_path)

@pytest.mark.asyncio
async def test_create_tables_error():
    """Test table creation failure."""
    Database._instance = None
    db = Database()
    
    # Mock connect to return a mock connection that fails on execute
    # But connect() calls _create_tables() internally.
    
    # We can patch _create_tables to fail? No, we want to test exception handling IN _create_tables
    # So we need conn.execute to fail.
    
    with patch('aiosqlite.connect') as mock_connect_cls:
        mock_conn = mock_connect_cls.return_value
        # Mock execute to raise exception
        mock_conn.execute.side_effect = Exception("Table Error")
        
        with pytest.raises(Exception):
            await db.connect()
