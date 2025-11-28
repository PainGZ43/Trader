import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class CustomFormatter(logging.Formatter):
    """
    Custom formatter to add colors to console output.
    """
    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
    
    FORMATS = {
        logging.DEBUG: Fore.CYAN + FORMAT + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + FORMAT + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + FORMAT + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class CallbackHandler(logging.Handler):
    """
    Custom handler to send logs to a callback (e.g., UI).
    """
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        try:
            msg = self.format(record)
            self.callback(record.levelno, msg)
        except Exception:
            self.handleError(record)

class Logger:
    _instance = None
    _loggers = {}
    _callback_handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Default level
        self.level = logging.INFO
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if env_level == "DEBUG":
            self.level = logging.DEBUG
        elif env_level == "WARNING":
            self.level = logging.WARNING
        elif env_level == "ERROR":
            self.level = logging.ERROR

    def add_callback(self, callback):
        """
        Register a callback for log messages.
        callback(level, message)
        """
        if self._callback_handler:
            return # Already registered
            
        self._callback_handler = CallbackHandler(callback)
        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s", datefmt='%H:%M:%S')
        self._callback_handler.setFormatter(formatter)
        
        # Add to existing loggers
        for logger in self._loggers.values():
            logger.addHandler(self._callback_handler)

    def get_logger(self, name):
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self.level)
        logger.propagate = False  # Prevent double logging

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)

        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "system.log"),
            maxBytes=10*1024*1024, # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Add Callback Handler if exists
        if self._callback_handler:
            logger.addHandler(self._callback_handler)

        self._loggers[name] = logger
        return logger

# Global accessor
def get_logger(name):
    return Logger().get_logger(name)
