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
        
        # Determine Mode based on Config (Default to Real if not specified)
        # We will refine this dynamically based on the Key Type later.
        self.base_url = self.BASE_URL_REAL
        self.is_mock_server = False

        # Override if explicitly set
        if config.get("KIWOOM_API_URL"):
            self.base_url = config.get("KIWOOM_API_URL")

        self.access_token = None
        self.token_expiry = None
        
        # Rate Limiter: Global (e.g., 5 requests per second)
        self.rate_limiter = RateLimiter(max_tokens=5, refill_rate=5)
        
        # Specific Rate Limiters for sensitive TRs
        self.specific_limiters = {
            "ka10004": RateLimiter(max_tokens=1, refill_rate=1), # Market Condition: 1 req/sec
            "opt10080": RateLimiter(max_tokens=1, refill_rate=0.5), # Minute Candle: 1 req/2sec (conservative)
        }
        
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
        # Check if current token is valid
        if self.access_token and self.token_expiry:
            now = datetime.now()
            if isinstance(self.token_expiry, datetime):
                if now < self.token_expiry - timedelta(minutes=1): # Buffer
                    return self.access_token

        # Lazy import to avoid circular dependency if any
        from data.key_manager import key_manager
        
        active_key = key_manager.get_active_key()
        if not active_key:
            self.logger.error("No active API key found. Please register a key in Settings.")
            return None

        app_key = active_key["app_key"]
        secret_key = active_key["secret_key"]
        key_type = active_key.get("type", "REAL")
        
        # Dynamically update base_url based on active key type
        if key_type == "MOCK":
            self.base_url = self.BASE_URL_MOCK
            self.is_mock_server = True
            self.logger.info("Using MOCK Key. Switching to Mock API Server.")
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
                        
                        # Handle Expiry
                        expires_in = result.get("expires_in") # Seconds (int)
                        expires_dt = result.get("expires_dt") # String
                        
                        if expires_in:
                            self.token_expiry = datetime.now() + timedelta(seconds=int(expires_in))
                        elif expires_dt:
                            # Format: YYYY-MM-DD HH:MM:SS
                            try:
                                self.token_expiry = datetime.strptime(expires_dt, "%Y-%m-%d %H:%M:%S")
                            except:
                                self.token_expiry = datetime.now() + timedelta(hours=6) # Default fallback
                        
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
        if not self.access_token:
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
        # Global Limit
        await self.rate_limiter.acquire()
        
        # Specific Limit (based on api_id or tr_id)
        target_id = api_id or tr_id
        if target_id and target_id in self.specific_limiters:
            await self.specific_limiters[target_id].acquire()
        
        if not self.access_token:
            token = await self.get_token()
            if not token:
                return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
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

    # --- Market Data ---

    async def get_current_price(self, symbol):
        endpoint = "/api/dostk/mrkcond"
        tr_id = "ka10004"
        data = {"stk_cd": symbol}
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def get_market_index(self, market_code):
        """
        Get Market Index (KOSPI: 001)
        """
        endpoint = "/api/dostk/mrkcond"
        tr_id = "ka10004"
        
        mrkt_tp = "1" # Default to KOSPI
        if market_code == "001":
            mrkt_tp = "1"
        elif market_code == "200":
            mrkt_tp = "2"
            
        data = {
            "mrkt_tp": mrkt_tp
        }
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def get_ohlcv(self, symbol, interval, start_date=None):
        """
        Get Historical Data (OHLCV).
        interval: "day" (opt10081) or "minute" (opt10080)
        """
        if interval == "day":
            endpoint = "/api/dostk/ohlcv_day" # Hypothetical endpoint for bridge
            tr_id = "opt10081"
        elif interval == "minute":
            endpoint = "/api/dostk/ohlcv_minute"
            tr_id = "opt10080"
        else:
            self.logger.error(f"Invalid interval: {interval}")
            return None
            
        data = {
            "stk_cd": symbol,
            "date": start_date, # YYYYMMDD
            "tick": "1" if interval == "minute" else None
        }
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def get_code_list(self, market_type="0"):
        """
        Get Stock Code List.
        market_type: "0" (KOSPI), "10" (KOSDAQ)
        """
        endpoint = "/api/dostk/code_list"
        tr_id = "GetCodeListByMarket" 
        
        data = {"market": market_type}
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    # --- Order Management ---

    async def send_order(self, symbol, order_type, qty, price=0, trade_type="00"):
        endpoint = "/api/dostk/ordr"
        
        # Determine TR ID based on Server Mode
        if self.is_mock_server:
            # Mock Server TR IDs (from PDF)
            if str(order_type) == "1": # Buy
                tr_id = "kt10000" # Mock might use same or different, usually same for Stock
            elif str(order_type) == "2": # Sell
                tr_id = "kt10001"
            else:
                tr_id = "kt10000" 
        else:
            # Real Server TR IDs
            if str(order_type) == "1": # Buy
                tr_id = "kt10000"
            elif str(order_type) == "2": # Sell
                tr_id = "kt10001"
            else:
                tr_id = "kt10000"
        
        data = {
            "dmst_stex_tp": "KRX",
            "stk_cd": symbol,
            "ord_qty": str(qty),
            "ord_uv": str(price),
            "trde_tp": trade_type,
            "cond_uv": "0" 
        }
        
        self.logger.info(f"Sending Order: {order_type} {symbol} {qty}@{price} (TR: {tr_id}, URL: {endpoint})")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def cancel_order(self, order_no, symbol, qty):
        endpoint = "/api/dostk/ordr"
        tr_id = "kt10003" 
        
        data = {
            "orig_ord_no": order_no, 
            "stk_cd": symbol,
            "cncl_qty": str(qty), 
            "dmst_stex_tp": "KRX"
        }
        
        self.logger.info(f"Canceling Order: {order_no} (TR: {tr_id}, URL: {endpoint})")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    # --- Account & Balance ---

    async def get_account_balance(self):
        """
        Get Account Balance and Withdrawable Cash.
        """
        endpoint = "/api/dostk/acnt"
        tr_id = "kt00018"
        
        from data.key_manager import key_manager
        active_key = key_manager.get_active_key()
        acc_no = active_key["account_no"] if active_key else ""
        
        data = {
            "qry_tp": "1",
            "dmst_stex_tp": "KRX",
            "acc_no": acc_no 
        }
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    # --- Condition Search ---

    async def get_condition_load(self):
        """
        Load Condition List.
        """
        endpoint = "/api/dostk/condition_load" 
        tr_id = "GetConditionLoad"
        
        # API requires a body, even if empty
        data = {}
        
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def send_condition(self, screen_no, condition_name, condition_index, search_type):
        """
        Send Condition Search Request.
        """
        endpoint = "/api/dostk/condition_send"
        tr_id = "SendCondition"
        
        data = {
            "screen_no": screen_no,
            "condition_name": condition_name,
            "condition_index": condition_index,
            "search_type": search_type
        }
        
        self.logger.info(f"Sending Condition: {condition_name} ({condition_index})")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

    async def stop_condition(self, screen_no, condition_name, condition_index):
        """
        Stop Condition Search Request.
        """
        endpoint = "/api/dostk/condition_stop"
        tr_id = "StopCondition"
        
        data = {
            "screen_no": screen_no,
            "condition_name": condition_name,
            "condition_index": condition_index
        }
        
        self.logger.info(f"Stopping Condition: {condition_name} ({condition_index})")
        return await self.request("POST", endpoint, data=data, api_id=tr_id)

kiwoom_client = KiwoomRestClient()
