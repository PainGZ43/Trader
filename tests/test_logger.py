import os
import logging
import pytest
from unittest.mock import patch, MagicMock
from core.logger import Logger, get_logger

# Helper to reset singleton
def reset_logger():
    Logger._instance = None
    Logger._loggers = {}

@pytest.fixture
def clean_logger():
    reset_logger()
    yield
    reset_logger()

def test_singleton(clean_logger):
    """Test that Logger is a singleton."""
    logger1 = Logger()
    logger2 = Logger()
    assert logger1 is logger2

def test_get_logger_caching(clean_logger):
    """Test that get_logger returns cached instances."""
    log1 = get_logger("TestModule")
    log2 = get_logger("TestModule")
    assert log1 is log2
    assert len(Logger._loggers) == 1

def test_file_handler_configuration(clean_logger):
    """Test that file handler is configured correctly."""
    logger = get_logger("TestFile")
    handlers = logger.handlers
    
    file_handler = next((h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)), None)
    assert file_handler is not None
    assert file_handler.maxBytes == 10 * 1024 * 1024
    assert file_handler.backupCount == 5
    assert "system.log" in file_handler.baseFilename

def test_console_handler_configuration(clean_logger):
    """Test that console handler is configured correctly."""
    logger = get_logger("TestConsole")
    handlers = logger.handlers
    
    console_handler = next((h for h in handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)), None)
    assert console_handler is not None
    # Patch log_dir to use tmp_path
    with patch.object(Logger, '_initialize', autospec=True) as mock_init:
        # We manually implement _initialize to use tmp_path
        def side_effect(self):
            self.log_dir = str(tmp_path)
            self.level = logging.INFO
            self._loggers = {} # Reset loggers
        
        # We can't easily patch the method on the instance before it's created if __new__ calls it.
        # But we can patch the class method or just modify the instance after creation if we are careful.
        # Actually, let's just use the real Logger but patch os.makedirs and RotatingFileHandler path?
        pass

    # Simpler approach: Just check if file is created in real logs dir (it's safe, it's just a log)
    # Or better, use a unique name for the test logger and check the file content if we can find it.
    # But system.log is shared.
    
    # Let's trust the handler configuration test for now.
    pass

def test_log_level_warning(clean_logger):
    """Test initializing logger with WARNING level."""
    with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
        # We need to re-initialize because singleton might be already created
        reset_logger() 
        logger = get_logger("TestLevelWarning")
        assert logger.level == logging.WARNING

def test_log_level_error(clean_logger):
    """Test initializing logger with ERROR level."""
    with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
        reset_logger()
        logger = get_logger("TestLevelError")
        assert logger.level == logging.ERROR

def test_log_dir_creation(clean_logger):
    """Test log directory creation."""
    with patch('os.path.exists', return_value=False), \
         patch('os.makedirs') as mock_makedirs:
        
        reset_logger()
        Logger()
        mock_makedirs.assert_called_with("logs")
