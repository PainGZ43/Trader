import asyncio
import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from data.websocket_client import ws_client
from data.data_collector import data_collector

# Setup logging to stdout
logger = get_logger("StartupCheck")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

async def main():
    print("--- Starting Components ---")
    
    # 1. KiwoomRestClient (Lazy init usually, but let's check token)
    # It might log warnings if keys are missing
    await kiwoom_client.get_token()
    
    # 2. WebSocketClient
    await ws_client.connect()
    
    # 3. DataCollector
    # This starts DB and other monitors
    # We mock db.connect to avoid locking real DB if possible, or just run it.
    # Let's run it but stop quickly.
    await data_collector.start()
    
    print("--- Components Started ---")
    await asyncio.sleep(5)
    
    print("--- Stopping Components ---")
    await data_collector.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
