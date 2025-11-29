import unittest
import asyncio
import os
import json
import aiosqlite
from unittest.mock import MagicMock, AsyncMock, patch

# Import modules
from core.config import ConfigLoader
from core.database import Database
from core.system_monitor import SystemMonitor

class TestCoreRefinement(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Config Setup
        self.config = ConfigLoader()
        self.test_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'settings.json')
        
    def tearDown(self):
        # Cleanup settings.json if created
        if os.path.exists(self.test_json_path):
            try:
                # Restore or delete? For test isolation, deleting is safer if we don't want to pollute.
                # But we should be careful not to delete real config if running on dev env.
                # In this mock env, it's fine.
                pass 
            except:
                pass

    def test_config_save(self):
        """Test ConfigLoader.save() persists data."""
        test_key = "TEST_UI_SETTING"
        test_val = "12345"
        
        self.config.save(test_key, test_val)
        
        # Verify in memory
        self.assertEqual(self.config.get(test_key), test_val)
        
        # Verify file
        self.assertTrue(os.path.exists(self.test_json_path))
        with open(self.test_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data.get(test_key), test_val)
            
        # Clean up
        # os.remove(self.test_json_path) # Optional

    async def test_database_migration(self):
        """Test Database creates schema_version and migrates."""
        db = Database()
        # Use memory db for testing to avoid touching real file
        db.db_path = ":memory:" 
        
        await db.connect()
        
        # Check if schema_version table exists
        async with db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'") as cursor:
            row = await cursor.fetchone()
            self.assertIsNotNone(row)
            
        # Check version is 1
        async with db.conn.execute("SELECT version FROM schema_version") as cursor:
            row = await cursor.fetchone()
            self.assertEqual(row['version'], 1)
            
        await db.close()

    async def test_system_monitor_kiwoom(self):
        """Test SystemMonitor checks Kiwoom server."""
        monitor = SystemMonitor()
        monitor._publish_warning = MagicMock()
        
        # Mock socket to fail
        with patch('socket.create_connection', side_effect=OSError("Mock Fail")):
            await monitor._check_kiwoom_server()
            monitor._publish_warning.assert_called_with("Kiwoom Server Unreachable", "Failed to connect to openapi.kiwoom.com")
            
        # Mock socket to success
        monitor._publish_warning.reset_mock()
        with patch('socket.create_connection', return_value=True):
            await monitor._check_kiwoom_server()
            monitor._publish_warning.assert_not_called()

if __name__ == "__main__":
    unittest.main()
