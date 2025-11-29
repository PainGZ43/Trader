import os
import pytest
import yaml
import json
from unittest.mock import patch, mock_open
from core.config import ConfigLoader

# Helper to reset singleton
def reset_config_loader():
    ConfigLoader._instance = None

@pytest.fixture
def clean_config():
    reset_config_loader()
    # Patch os.environ to be empty to avoid interference from real env
    with patch.dict(os.environ, {}, clear=True):
        yield
    reset_config_loader()

def test_default_values(clean_config):
    """Test that default values are loaded correctly."""
    # We need to ensure load_dotenv doesn't crash or set things we don't want.
    # Since we cleared environ, load_dotenv might try to load from real .env if we don't mock it.
    # But ConfigLoader now uses explicit path.
    # We should probably mock os.path.exists to return False for .env to avoid loading real one.
    
    with patch('os.path.exists', return_value=False):
        config = ConfigLoader()
        assert config.get('LOG_LEVEL') == 'INFO'
        assert config.get('MOCK_MODE') is False
        assert config.get('DB_PATH') == 'trade.db'

def test_yaml_loading(clean_config):
    """Test loading from settings.yaml."""
    yaml_content = {'MOCK_MODE': True, 'LOG_LEVEL': 'DEBUG'}
    
    with patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=yaml.dump(yaml_content))):
        
        def side_effect(path):
            # Return True for settings.yaml, False for .env (to avoid load_dotenv parsing yaml)
            return 'settings.yaml' in str(path)
        mock_exists.side_effect = side_effect
        
        config = ConfigLoader()
        assert config.get('MOCK_MODE') is True
        assert config.get('LOG_LEVEL') == 'DEBUG'

def test_json_loading(clean_config):
    """Test loading from settings.json."""
    json_content = json.dumps({'MOCK_MODE': True, 'KIWOOM_API_URL': 'http://json-url'})
    
    with patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=json_content)):
        
        def side_effect(path):
            return 'settings.json' in str(path)
        mock_exists.side_effect = side_effect
        
        config = ConfigLoader()
        assert config.get('MOCK_MODE') is True
        assert config.get('KIWOOM_API_URL') == 'http://json-url'

def test_priority_env_over_yaml(clean_config):
    """Test that Environment Variables override YAML."""
    yaml_content = yaml.dump({'MOCK_MODE': False, 'LOG_LEVEL': 'DEBUG'})
    
    # We set env vars in the patch.dict context
    with patch.dict(os.environ, {'MOCK_MODE': 'True', 'LOG_LEVEL': 'WARNING'}), \
         patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=yaml_content)):
        
        def side_effect(path):
            return 'settings.yaml' in str(path)
        mock_exists.side_effect = side_effect
        
        config = ConfigLoader()
        assert config.get('MOCK_MODE') is True 
        assert config.get('LOG_LEVEL') == 'WARNING'

def test_malformed_yaml(clean_config):
    """Test handling of malformed YAML."""
    with patch('builtins.open', mock_open(read_data="invalid: yaml: content: :")), \
         patch('os.path.exists', return_value=True), \
         patch('yaml.safe_load', side_effect=Exception("YAML Error")):
        
        config = ConfigLoader()
        # Should not crash

def test_malformed_json(clean_config):
    """Test handling of malformed JSON."""
    with patch('builtins.open', mock_open(read_data="{invalid json}")), \
         patch('os.path.exists', return_value=True), \
         patch('json.load', side_effect=Exception("JSON Error")):
        
        config = ConfigLoader()
        # Should not crash

def test_set_config(clean_config):
    """Test set method."""
    config = ConfigLoader()
    config.set("NEW_KEY", "NEW_VAL")
    assert config.get("NEW_KEY") == "NEW_VAL"

