import keyring
import logging
from core.logger import get_logger

class SecureStorage:
    """
    Manages secure storage of sensitive data using OS Keyring.
    Service name is 'PainTrader'.
    """
    SERVICE_NAME = "PainTrader"

    def __init__(self):
        self.logger = get_logger("SecureStorage")

    def save(self, key: str, value: str):
        """
        Save a value securely.
        """
        try:
            keyring.set_password(self.SERVICE_NAME, key, value)
            self.logger.info(f"Securely saved key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to save key {key}: {e}")
            raise

    def get(self, key: str) -> str:
        """
        Retrieve a value securely.
        """
        try:
            value = keyring.get_password(self.SERVICE_NAME, key)
            if value:
                self.logger.debug(f"Successfully retrieved key: {key}")
            else:
                self.logger.warning(f"Key not found: {key}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to retrieve key {key}: {e}")
            return None

    def delete(self, key: str):
        """
        Delete a value.
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
            self.logger.info(f"Deleted key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to delete key {key}: {e}")

secure_storage = SecureStorage()
