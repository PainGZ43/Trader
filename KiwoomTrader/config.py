import os
from dotenv import load_dotenv
from settings_manager import settings

load_dotenv()

class Config:
    # Static Configs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH = "sqlite:///kiwoom_trader.db"
    
    # Dynamic Configs (from settings.json)
    @property
    def APP_KEY(self): return settings.get("APP_KEY")
    
    @property
    def SECRET_KEY(self): return settings.get("SECRET_KEY")
    
    @property
    def ACCOUNT_NO(self): return settings.get("ACCOUNT_NO")
    
    @property
    def KAKAO_ACCESS_TOKEN(self): return settings.get("KAKAO_ACCESS_TOKEN")
    
    @property
    def KAKAO_REFRESH_TOKEN(self): return settings.get("KAKAO_REFRESH_TOKEN")
    
    @property
    def IS_VIRTUAL(self): return settings.get("IS_VIRTUAL", True)

# Global Instance
Config = Config()

