import os
import sys
import platform

def get_app_data_dir(app_name="PainTrader"):
    """
    Get the application data directory.
    - Windows: %APPDATA%/app_name
    - Linux/Mac: ~/.app_name
    """
    if platform.system() == "Windows":
        base_path = os.getenv("APPDATA")
    else:
        base_path = os.path.expanduser("~")
        app_name = f".{app_name.lower()}" # Hidden dir on Unix

    app_dir = os.path.join(base_path, app_name)
    
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)
        
    return app_dir

def get_log_dir(app_name="PainTrader"):
    log_dir = os.path.join(get_app_data_dir(app_name), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_db_path(app_name="PainTrader", db_name="trade.db"):
    return os.path.join(get_app_data_dir(app_name), db_name)

def get_config_path(app_name="PainTrader", config_name="settings.json"):
    return os.path.join(get_app_data_dir(app_name), config_name)
