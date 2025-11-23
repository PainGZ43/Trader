import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from core.config import config
from core.logger import get_logger
from data.rate_limiter import RateLimiter

class KiwoomRestClient:
    """
    Official Kiwoom REST API Client.
    Handles OAuth2 authentication, token management, and HTTP requests.
    """
    # Base URLs
    BASE_URL_REAL = "https://api.kiwoom.com" 
    BASE_URL_MOCK = "https://mockapi.kiwoom.com"

    def __init__(self):
        self.logger = get_logger("KiwoomRestClient")
        
        # Determine Mode
        self.is_mock_server = config.get("MOCK_MODE", True) 
        self.offline_mode = False 
        
        if self.is_mock_server:
            self.base_url = self.BASE_URL_MOCK
            self.logger.info("Initialized in MOCK SERVER Mode")
        else:
            self.base_url = self.BASE_URL_REAL
            self.logger.info("Initialized in REAL SERVER Mode")

        # Override if explicitly set
        if config.get("KIWOOM_API_URL"):
            self.base_url = config.get("KIWOOM_API_URL")

        self.access_token = None
        self.token_expiry = None
        
        # Rate Limiter: e.g., 5 requests per second
        self.rate_limiter = RateLimiter(max_tokens=5, refill_rate=5)
        
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

    async def get_token(self):
        """
        Issue Access Token using KeyManager's active key.
        """
        if self.offline_mode:
            self.logger.info("[OFFLINE] Token issued successfully.")
            self.access_token = "MOCK_TOKEN"
            return self.access_token

        # Lazy import to avoid circular dependency if any
        from data.key_manager import key_manager
        
        active_key = key_manager.get_active_key()
        if not active_key:
            self.logger.error("No active API key found. Please register a key in Settings.")
            return None

        app_key = active_key["app_key"]
        secret_key = active_key["secret_key"]
        
        # Dynamically update base_url based on active key type
        # This ensures we use the correct server even if config hasn't reloaded
        if active_key.get("type") == "MOCK":
            self.base_url = self.BASE_URL_MOCK
            self.is_mock_server = True
        else:
            self.base_url = self.BASE_URL_REAL
            self.is_mock_server = False
            
        url = f"{self.base_url}/oauth2/token"
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "secretkey": secret_key
        }

        self.logger.info(f"Issuing new Access Token... (Target: {self.base_url})")
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Token Response Data: {result}") 
                    
                    token = result.get("token") or result.get("access_token")
                    if token:
                        self.access_token = token
                        self.token_expiry = result.get("expires_dt") or result.get("expires_in")
                        self.logger.info(f"Token issued successfully. Expires: {self.token_expiry}")
                        return self.access_token
                    else:
                        msg = result.get("return_msg") or result.get("error_description") or "Unknown Error"
                        code = result.get("return_code") or result.get("error")
                        self.logger.error(f"Token issuance failed: {msg} (Code: {code})")
                        return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Token issuance failed: {error_text}")
                    return None
        except Exception as e:
            self.logger.error(f"Token issuance error: {e}")
            return None

    async def revoke_token(self):
        """
        Revoke Access Token.
        """
        if self.offline_mode or not self.access_token:
            return True

        from data.key_manager import key_manager
        active_key = key_manager.get_active_key()
        if not active_key:
            return False

        session = await self._get_session()
        url = f"{self.base_url}/oauth2/revoke"
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        data = {
            "token": self.access_token,
            "token_type_hint": "access_token",
            "appkey": active_key["app_key"],
            "secretkey": active_key["secret_key"]
        }

        self.logger.info(f"Revoking Access Token...")
        
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    self.logger.info("Token revoked successfully.")
                    self.access_token = None
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Token revocation failed: {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"Token revocation error: {e}")
            return False

    async def request(self, method, endpoint, params=None, data=None, api_id=None, tr_id=None):
        """
        Wrapper for HTTP requests with Rate Limiting and Auto Auth.
        """
        if self.offline_mode:
            self.logger.debug(f"[OFFLINE] Request: {method} {endpoint} TR:{tr_id}")
            return self._get_mock_response(endpoint, tr_id, data)

        await self.rate_limiter.acquire()
        
        if not self.access_token:
            token = await self.get_token()
            if not token:
                return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # Some endpoints might need appkey/secret in headers too? 
        # Usually Bearer token is enough for OAuth2.
        # But if needed, we can add them.
        
        if tr_id:
            headers["tr_id"] = tr_id
        if api_id:
            headers["api-id"] = api_id
        
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, headers=headers, params=params, json=data) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401: # Unauthorized, maybe token expired
                    self.logger.warning("401 Unauthorized. Retrying with new token...")
                    self.access_token = None
                    token = await self.get_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                        async with session.request(method, url, headers=headers, params=params, json=data) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.json()
                    return None
                else:
                    text = await response.text()
                    self.logger.error(f"API Request Failed [{method} {endpoint}]: {response.status} - {text}")
                    return None
        except Exception as e:
            self.logger.error(f"Request exception: {e}")
            return None

    def _get_mock_response(self, endpoint, tr_id, data):
        """Helper to generate mock responses."""
        if "stock/price" in endpoint or tr_id == "FHKST01010100" or "mrkcond" in endpoint or tr_id == "ka10004": 
            return {"output": {"price": "70000", "change": "+1.0", "volume": "1000000"}}
        elif "order" in endpoint or tr_id == "TT80012" or tr_id == "ct80012": 
            return {"rt_cd": "0", "msg_cd": "0000", "msg1": "Order Accepted", "output": {"order_no": "123456"}}
        elif "balance" in endpoint or tr_id == "OPW00018":
            return {"output": [{"code": "005930", "name": "Samsung Elec", "qty": "10", "avg_price": "68000"}]}
        return {}

    # --- Market Data ---

    async def get_current_price(self, symbol):
        endpoint = "/api/dostk/mrkcond"
        tr_id = "ka10004"
        data = {"stk_cd": symbol}
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    # --- Order Management ---

    async def send_order(self, symbol, order_type, qty, price=0, trade_type="00"):
        endpoint = "/api/dostk/order"
        tr_id = "ct80012"
        
        # Need account number from active key or storage
        from data.key_manager import key_manager
        active_key = key_manager.get_active_key()
        acc_no = active_key["account_no"] if active_key else ""
        
        data = {
            "acc_no": acc_no,
            "order_type": order_type, 
            "stk_cd": symbol,
            "qty": str(qty),
            "price": str(price),
            "trade_type": trade_type 
        }
        
        self.logger.info(f"Sending Order: {order_type} {symbol} {qty}@{price}")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def cancel_order(self, order_no, symbol, qty):
        endpoint = "/api/dostk/order_cancel"
        tr_id = "ct80013"
        
        from data.key_manager import key_manager
        active_key = key_manager.get_active_key()
        acc_no = active_key["account_no"] if active_key else ""
        
        data = {
            "acc_no": acc_no,
            "order_no": order_no,
            "stk_cd": symbol,
            "qty": str(qty)
        }
        
        self.logger.info(f"Canceling Order: {order_no}")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    # --- Account & Balance ---

    async def get_account_balance(self):
        endpoint = "/api/dostk/balance"
        tr_id = "opw00018"
        
        from data.key_manager import key_manager
        active_key = key_manager.get_active_key()
        acc_no = active_key["account_no"] if active_key else ""
        
        data = {
            "acc_no": acc_no
        }
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

kiwoom_client = KiwoomRestClient()
