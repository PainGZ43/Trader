import os
from dotenv import load_dotenv

class ConfigLoader:
    """
    Loads configuration from environment variables (.env) and provides access to them.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        load_dotenv()
        self._config = {}
        
        # Load essential configs
        self._config['KIWOOM_APP_KEY'] = os.getenv('KIWOOM_APP_KEY')
        self._config['KIWOOM_SECRET_KEY'] = os.getenv('KIWOOM_SECRET_KEY')
        self._config['ACCOUNT_NO'] = os.getenv('ACCOUNT_NO')
        self._config['KAKAO_ACCESS_TOKEN'] = os.getenv('KAKAO_ACCESS_TOKEN')
        self._config['KAKAO_REFRESH_TOKEN'] = os.getenv('KAKAO_REFRESH_TOKEN')
        self._config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
        self._config['DB_PATH'] = os.getenv('DB_PATH', 'trade.db')

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        # Note: This does not persist to .env file automatically. 
        # Persistence logic would be needed if we want to save changes.

config = ConfigLoader()
