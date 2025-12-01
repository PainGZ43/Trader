import pytest
import os
import sys
import shutil
from unittest.mock import patch, MagicMock
from core.utils import get_app_data_dir, get_log_dir, get_db_path, get_config_path
from core.config import ConfigLoader
from core.logger import Logger
from core.database import Database

# Helper to reset singletons
def reset_singletons():
    ConfigLoader._instance = None
    Logger._instance = None
    Logger._loggers = {}
    Database._instance = None

@pytest.fixture
def mock_app_data(tmp_path):
    """
    Mock APPDATA environment variable to use a temporary directory.
    """
    mock_dir = tmp_path / "MockAppData"
    mock_dir.mkdir()
    
    # We use patch.dict to update os.environ, preserving other vars but overwriting APPDATA
    env_vars = {"APPDATA": str(mock_dir)}
    if sys.platform != "win32":
        env_vars["HOME"] = str(mock_dir)
        
    with patch.dict(os.environ, env_vars):
        # For non-Windows, we might need to patch expanduser if utils.py uses it
        if sys.platform != "win32":
            with patch("os.path.expanduser", return_value=str(mock_dir)):
                yield mock_dir
        else:
            yield mock_dir

def test_utils_paths(mock_app_data):
    """
    Verify that utility functions return paths inside the mocked AppData directory.
    """
    app_name = "PainTrader"
    
    # 1. App Data Dir
    app_dir = get_app_data_dir(app_name)
    assert str(mock_app_data) in app_dir
    assert app_name in app_dir
    assert os.path.exists(app_dir)
    
    # 2. Log Dir
    log_dir = get_log_dir(app_name)
    assert os.path.join(app_dir, "logs") == log_dir
    assert os.path.exists(log_dir)
    
    # 3. DB Path
    db_path = get_db_path(app_name)
    assert os.path.join(app_dir, "trade.db") == db_path
    
    # 4. Config Path
    config_path = get_config_path(app_name)
    assert os.path.join(app_dir, "settings.json") == config_path

def test_config_loader_paths(mock_app_data):
    """
    Verify that ConfigLoader uses the correct AppData path for DB_PATH by default.
    """
    reset_singletons()
    
    # Ensure no env var overrides DB_PATH, but keep APPDATA
    with patch.dict(os.environ):
        if "DB_PATH" in os.environ:
            del os.environ["DB_PATH"]
            
        # Mock os.path.exists to hide local settings.json/yaml
        original_exists = os.path.exists
        def side_effect(path):
            if "settings.json" in str(path) or "settings.yaml" in str(path):
                if str(mock_app_data) in str(path):
                    return original_exists(path)
                return False 
            return original_exists(path)
            
        with patch("os.path.exists", side_effect=side_effect):
            # Patch load_dotenv to prevent loading .env file
            with patch("core.config.load_dotenv"):
                config = ConfigLoader()
                
                expected_db_path = get_db_path()
                assert config.get("DB_PATH") == expected_db_path
                assert str(mock_app_data) in config.get("DB_PATH")

def test_logger_file_creation(mock_app_data):
    """
    Verify that Logger creates the log file in the AppData/logs directory.
    """
    reset_singletons()
    
    logger = Logger()
    log = logger.get_logger("TestLogger")
    log.info("Test Log Message")
    
    log_dir = get_log_dir()
    log_file = os.path.join(log_dir, "system.log")
    
    assert os.path.exists(log_file)
    
    with open(log_file, "r") as f:
        content = f.read()
        assert "Test Log Message" in content

@pytest.mark.asyncio
async def test_database_connection_path(mock_app_data):
    """
    Verify that Database connects to the file in AppData.
    """
    reset_singletons()
    
    # Ensure Config is loaded with default paths (pointing to AppData)
    with patch.dict(os.environ):
        if "DB_PATH" in os.environ:
            del os.environ["DB_PATH"]
        
        original_exists = os.path.exists
        def side_effect(path):
            if "settings.json" in str(path) or "settings.yaml" in str(path):
                if str(mock_app_data) in str(path):
                    return original_exists(path)
                return False
            return original_exists(path)

        with patch("os.path.exists", side_effect=side_effect):
            with patch("core.config.load_dotenv"):
                config_instance = ConfigLoader() # Initialize config
                
                # Patch the config object in database module
                with patch("core.database.config", config_instance):
                    db = Database()
                    await db.connect()
                    
                    expected_db_path = get_db_path()
                    
                    # Check if the file exists
                    assert os.path.exists(expected_db_path)
                    
                    # Verify connection (create a table)
                    await db.execute("CREATE TABLE IF NOT EXISTS path_test (id INTEGER PRIMARY KEY)")
                    
                    await db.close()
                    
                    # Verify file still exists and has size > 0
                    assert os.path.getsize(expected_db_path) > 0
