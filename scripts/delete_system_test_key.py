import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.key_manager import key_manager
from core.logger import get_logger

logger = get_logger("DeleteKey")

def delete_system_test_key():
    keys = key_manager.get_keys()
    target_uuid = None
    
    for k in keys:
        if k["owner"] == "SystemTest":
            target_uuid = k["uuid"]
            break
            
    if target_uuid:
        logger.info(f"Found SystemTest key with UUID: {target_uuid}")
        if key_manager.delete_key(target_uuid):
            logger.info("Successfully deleted SystemTest key.")
        else:
            logger.error("Failed to delete SystemTest key.")
    else:
        logger.warning("SystemTest key not found.")

if __name__ == "__main__":
    delete_system_test_key()
