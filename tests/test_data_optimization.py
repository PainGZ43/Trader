import unittest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from core.database import Database
from data.data_collector import DataCollector

class TestDataOptimization(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.db = Database()
        self.db.db_path = ":memory:"
        await self.db.connect()
        
        self.collector = DataCollector()
        self.collector.rest_client = AsyncMock()
        
        # Patch db in collector to use our memory db
        # Since DataCollector imports db instance, we need to patch 'data.data_collector.db'
        # But here we can just set it if we could, but it's imported.
        # Easier to patch the method or use the global db instance if it's singleton.
        # The singleton 'db' in core.database is what we want to test.
        # But DataCollector imports 'db' from core.database.
        # So if we modify Database._instance or similar?
        # Actually, let's just patch 'data.data_collector.db'
        pass

    async def asyncTearDown(self):
        await self.db.close()

    async def test_database_execute_many(self):
        """Test Database.execute_many."""
        # Create table
        await self.db.execute("CREATE TABLE test_bulk (id INTEGER PRIMARY KEY, name TEXT)")
        
        data = [(1, "A"), (2, "B"), (3, "C")]
        count = await self.db.execute_many("INSERT INTO test_bulk (id, name) VALUES (?, ?)", data)
        
        self.assertEqual(count, 3)
        
        rows = await self.db.fetch_all("SELECT * FROM test_bulk")
        self.assertEqual(len(rows), 3)

    async def test_fill_gap_bulk(self):
        """Test fill_gap uses bulk insert and parses timestamps."""
        # Mock REST response
        mock_ohlcv = {
            "output": [
                {"date": "20231001090000", "open": "100", "high": "110", "low": "90", "close": "105", "volume": "1000"},
                {"date": "20231001", "time": "090100", "open": "105", "high": "115", "low": "100", "close": "110", "volume": "2000"},
                {"date": "invalid", "close": "0"} # Should be skipped
            ]
        }
        self.collector.rest_client.get_ohlcv.return_value = mock_ohlcv
        
        # Patch db.execute_many in DataCollector
        with patch("data.data_collector.db.execute_many", new_callable=AsyncMock) as mock_exec_many:
            mock_exec_many.return_value = 2
            
            await self.collector.fill_gap("005930", datetime.now(), datetime.now())
            
            mock_exec_many.assert_called_once()
            args = mock_exec_many.call_args[0]
            query = args[0]
            data = args[1]
            
            self.assertEqual(len(data), 2)
            # Check first item timestamp (YYYYMMDDHHMMSS)
            self.assertEqual(data[0][0], datetime(2023, 10, 1, 9, 0, 0))
            # Check second item timestamp (YYYYMMDD + HHMMSS)
            self.assertEqual(data[1][0], datetime(2023, 10, 1, 9, 1, 0))

    async def test_sync_symbol_master_bulk(self):
        """Test sync_symbol_master uses bulk insert."""
        self.collector.rest_client.get_code_list.side_effect = [
            ["000001", "000002"], # KOSPI
            ["100001"] # KOSDAQ
        ]
        
        with patch("data.data_collector.db.execute_many", new_callable=AsyncMock) as mock_exec_many:
            await self.collector.sync_symbol_master()
            
            self.assertEqual(mock_exec_many.call_count, 2)
            
            # Check first call (KOSPI)
            args1 = mock_exec_many.call_args_list[0][0]
            data1 = args1[1]
            self.assertEqual(len(data1), 2)
            self.assertEqual(data1[0], ("000001", "", "KOSPI"))

if __name__ == "__main__":
    unittest.main()
