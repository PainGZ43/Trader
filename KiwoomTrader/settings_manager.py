import json
import os
from typing import Dict, Any

SETTINGS_FILE = "settings.json"

class SettingsManager:
    DEFAULT_SETTINGS = {
        "APP_KEY": "",
        "SECRET_KEY": "",
        "KAKAO_ACCESS_TOKEN": "",
        "KAKAO_REFRESH_TOKEN": "",
        "ACCOUNT_NO": "",
        "IS_VIRTUAL": True,  # True: Mock Investment (VTS), False: Real
        "AUTO_LOGIN": False
    }

    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        if not os.path.exists(SETTINGS_FILE):
            return self.DEFAULT_SETTINGS.copy()
        
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception as e:
            print(f"Failed to load settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, new_settings: Dict[str, Any]):
        self.settings.update(new_settings)
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value
        self.save_settings({key: value})

# Global Instance
settings = SettingsManager()
