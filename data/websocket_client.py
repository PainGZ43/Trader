import asyncio
import websockets
import json
from core.config import config
from core.logger import get_logger
from core.secure_storage import secure_storage

class WebSocketClient:
    """
    WebSocket Client for Kiwoom Real-time API.
    Handles connection, subscription, and message dispatch.
    """
    # ... (comments) ...
    
    def __init__(self):
        self.logger = get_logger("WebSocketClient")
        
        # Try SecureStorage first, then Config
        self.app_key = secure_storage.get("KIWOOM_APP_KEY") or config.get("KIWOOM_APP_KEY")
        self.secret_key = secure_storage.get("KIWOOM_SECRET_KEY") or config.get("KIWOOM_SECRET_KEY")
        self.ws_url = config.get("KIWOOM_WS_URL")
        self.mock_mode = config.get("MOCK_MODE", True)
        
        self.websocket = None
        self.is_connected = False
        self.callbacks = [] # List of functions to call when data arrives
        self._stop_event = asyncio.Event()

    async def connect(self):
        """
        Establish WebSocket connection.
        """
        if self.mock_mode:
            self.logger.info("[MOCK] WebSocket Connected (Simulated)")
            self.is_connected = True
            self._stop_event.clear()
            asyncio.create_task(self._mock_stream())
            return

        self.logger.info(f"Connecting to WebSocket: {self.ws_url}")
        self._stop_event.clear()
        
        # Get Access Token from RestClient (assuming it's shared or we need to get it)
        from data.kiwoom_rest_client import kiwoom_client
        token = await kiwoom_client.get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        try:
            # Try with extra_headers first (Standard)
            self.websocket = await websockets.connect(self.ws_url, extra_headers=headers)
            self.is_connected = True
            self.logger.info("WebSocket Connected")
            self.last_msg_time = asyncio.get_event_loop().time()
            asyncio.create_task(self._listen())
            asyncio.create_task(self._monitor_connection())
        except TypeError as e:
            if "unexpected keyword argument 'extra_headers'" in str(e):
                self.logger.warning("websockets.connect failed with extra_headers. Retrying without headers...")
                try:
                    self.websocket = await websockets.connect(self.ws_url)
                    self.is_connected = True
                    self.logger.info("WebSocket Connected (No Headers)")
                    self.last_msg_time = asyncio.get_event_loop().time()
                    asyncio.create_task(self._listen())
                    asyncio.create_task(self._monitor_connection())
                except Exception as e2:
                    self.logger.error(f"WebSocket Connection Failed (Retry): {e2}")
                    await self._reconnect()
            else:
                self.logger.error(f"WebSocket Connection Failed: {e}")
                await self._reconnect()
        except Exception as e:
            self.logger.error(f"WebSocket Connection Failed: {e}")
            await self._reconnect()

    async def _reconnect(self):
        """
        Reconnect with exponential backoff.
        """
        backoff = 1
        max_backoff = 60
        
        while not self._stop_event.is_set():
            self.logger.info(f"Reconnecting in {backoff} seconds...")
            await asyncio.sleep(backoff)
            
            try:
                await self.connect()
                if self.is_connected:
                    self.logger.info("Reconnection Successful")
                    # Re-subscribe if needed (logic to be added)
                    return
            except Exception as e:
                self.logger.error(f"Reconnection failed: {e}")
            
            backoff = min(backoff * 2, max_backoff)

    async def _monitor_connection(self):
        """
        Watchdog to detect silent disconnects.
        """
        while self.is_connected and not self._stop_event.is_set():
            await asyncio.sleep(10)
            if not self.last_msg_time:
                continue
                
            elapsed = asyncio.get_event_loop().time() - self.last_msg_time
            if elapsed > 60: # No data for 60s
                self.logger.warning(f"No data for {elapsed:.1f}s. Triggering reconnect...")
                self.is_connected = False
                if self.websocket:
                    await self.websocket.close()
                await self._reconnect()
                break

    def _switch_to_mock(self):
        self.logger.warning("Switching to MOCK MODE due to connection failure.")
        self.mock_mode = True
        self.is_connected = True
        asyncio.create_task(self._mock_stream())

    async def _mock_stream(self):
        """
        Simulate real-time data stream.
        """
        import random
        symbols = ["005930", "000660", "035420"]
        while not self._stop_event.is_set():
            await asyncio.sleep(1) # 1 second interval
            symbol = random.choice(symbols)
            price = random.randint(50000, 100000)
            change = random.choice(["+0.5%", "-0.2%", "+1.2%", "0.0%"])
            volume = random.randint(1000, 10000)
            
            data = {
                "code": symbol,
                "price": price,
                "change": change,
                "volume": volume,
                "type": "REALTIME"
            }
            await self._handle_message(json.dumps(data))

    async def disconnect(self):
        """
        Close WebSocket connection.
        """
        self._stop_event.set()
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False
        self.logger.info("WebSocket Disconnected")

    async def subscribe(self, tr_id, tr_key):
        """
        Send subscription request.
        """
        if self.mock_mode:
            self.logger.info(f"[MOCK] Subscribed to {tr_key}")
            return

        if not self.is_connected:
            self.logger.warning("Cannot subscribe: WebSocket not connected")
            return

        # Get Token
        from data.kiwoom_rest_client import kiwoom_client
        token = kiwoom_client.access_token
        if not token:
            self.logger.warning("Cannot subscribe: No Access Token")
            return

        payload = {
            "header": {
                "token": token, 
                "tr_type": "3" # Register
            },
            "body": {
                "tr_id": tr_id,
                "tr_key": tr_key
            }
        }
        
        try:
            await self.websocket.send(json.dumps(payload))
            self.logger.info(f"Subscribed to {tr_key} ({tr_id})")
        except Exception as e:
            self.logger.error(f"Subscription failed: {e}")

    async def _listen(self):
        """
        Listen for incoming messages.
        """
        try:
            while not self._stop_event.is_set():
                if not self.websocket:
                    break
                    
                message = await self.websocket.recv()
                self.last_msg_time = asyncio.get_event_loop().time()
                await self._handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket Connection Closed")
            self.is_connected = False
            await self._reconnect()
        except Exception as e:
            self.logger.error(f"WebSocket Listen Error: {e}")
            if not self._stop_event.is_set():
                 await self._reconnect()

    async def _handle_message(self, message):
        """
        Parse and dispatch message.
        """
        try:
            data = json.loads(message)
            # Dispatch to registered callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON received: {message}")

    def add_callback(self, callback):
        self.callbacks.append(callback)

ws_client = WebSocketClient()
