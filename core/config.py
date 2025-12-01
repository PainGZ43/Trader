import os
import yaml
import json
from dotenv import load_dotenv

from core.utils import get_config_path
import shutil

class ConfigLoader:
    """
    Loads configuration from environment variables (.env), YAML, and JSON files.
    Priority: Environment Variables > AppData JSON > Local JSON > YAML > Defaults
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Project Root Directory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load .env explicitly
        env_path = os.path.join(root_dir, '.env')
        load_dotenv(env_path)
        
        self._config = {}
        
        # 1. Default Values
        # 1. Default Values
        self._config['LOG_LEVEL'] = 'INFO'
        from core.utils import get_db_path
        self._config['DB_PATH'] = get_db_path()
        self._config['KIWOOM_API_URL'] = 'https://openapi.kiwoom.com/openapi/v1'
        self._config['KIWOOM_WS_URL'] = 'wss://openapi.kiwoom.com/websocket/v1'
        self._config['MOCK_MODE'] = False

        # 2. Load YAML (config/settings.yaml) - Read Only Template
        yaml_path = os.path.join(root_dir, 'config', 'settings.yaml')
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._config.update(yaml_config)
            except Exception as e:
                print(f"Warning: Failed to load settings.yaml: {e}")

        # 3. Load Local JSON (config/settings.json) - Read Only Template
        local_json_path = os.path.join(root_dir, 'config', 'settings.json')
        if os.path.exists(local_json_path):
            try:
                with open(local_json_path, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)
                    if json_config:
                        self._config.update(json_config)
            except Exception as e:
                print(f"Warning: Failed to load local settings.json: {e}")
        
        # 4. Load User JSON (AppData/PainTrader/settings.json) - Writable
        user_json_path = get_config_path()
        if os.path.exists(user_json_path):
            try:
                with open(user_json_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    if user_config:
                        self._config.update(user_config)
            except Exception as e:
                print(f"Warning: Failed to load user settings.json: {e}")
        
        # 5. Load Environment Variables (Override)
        env_keys = [
            'KIWOOM_APP_KEY', 'KIWOOM_SECRET_KEY', 'ACCOUNT_NO', 
            'KAKAO_APP_KEY', 'KAKAO_ACCESS_TOKEN', 'KAKAO_REFRESH_TOKEN', 
            'LOG_LEVEL', 'DB_PATH', 'KIWOOM_API_URL', 'KIWOOM_WS_URL', 'MOCK_MODE'
        ]
        
        for key in env_keys:
            val = os.getenv(key)
            if val is not None:
                if key == 'MOCK_MODE':
                    self._config[key] = val.lower() == 'true'
                else:
                    self._config[key] = val

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        # Note: This does not persist to .env file automatically. 

    def save(self, key, value):
        """
        Update config and persist to AppData/PainTrader/settings.json.
        """
        self.set(key, value)
        self.save_to_file()

    def save_to_file(self):
        """
        Save current configuration to AppData/PainTrader/settings.json.
        """
        json_path = get_config_path()
        
        # Load existing JSON to preserve structure if possible
        current_json = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    current_json = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to read existing user settings.json: {e}")
        
        sensitive_keys = [
            'KIWOOM_APP_KEY', 'KIWOOM_SECRET_KEY', 'ACCOUNT_NO', 
            'KAKAO_APP_KEY'
        ]
        
        # Update current_json with self._config, excluding sensitive keys
        for k, v in self._config.items():
            if k not in sensitive_keys:
                current_json[k] = v
                
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(current_json, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings.json: {e}")

config = ConfigLoader()
