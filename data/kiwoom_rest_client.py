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
        # Global Cooldown Check
        if hasattr(self, '_token_cooldown_until') and datetime.now() < self._token_cooldown_until:
            self.logger.warning(f"Token issuance is on cooldown until {self._token_cooldown_until.strftime('%H:%M:%S')}")
            return None
        # Check if current token is valid
        if self.access_token and self.token_expiry:
            now = datetime.now()
            if isinstance(self.token_expiry, datetime):
                if now < self.token_expiry - timedelta(minutes=1): # Buffer
                    return self.access_token

        # Lazy import to avoid circular dependency if any
        from data.key_manager import key_manager
        from core.secure_storage import secure_storage
        
        # 1. Check Memory Cache
        if self.access_token and self.token_expiry:
            now = datetime.now()
            if isinstance(self.token_expiry, datetime):
                if now < self.token_expiry - timedelta(minutes=1): # Buffer
                    return self.access_token

        # 2. Check Persistent Storage
        stored_token = secure_storage.get("kiwoom_access_token")
        stored_expiry = secure_storage.get("kiwoom_token_expiry")
        
        if stored_token and stored_expiry:
            try:
                expiry_dt = datetime.fromisoformat(stored_expiry)
                if datetime.now() < expiry_dt - timedelta(minutes=1):
                    self.access_token = stored_token
                    self.token_expiry = expiry_dt
                    self.logger.info(f"Restored valid token from storage. Expires: {expiry_dt}")
                    return self.access_token
            except:
                pass # Invalid format, ignore

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
                        
                        # Save to Persistent Storage
                        secure_storage.save("kiwoom_access_token", self.access_token)
                        secure_storage.save("kiwoom_token_expiry", self.token_expiry.isoformat())

                        self.logger.info(f"Token issued successfully. Expires: {self.token_expiry}")
                        return self.access_token
                    else:
                        msg = result.get("return_msg") or result.get("error_description") or "Unknown Error"
                        code = result.get("return_code") or result.get("error")
                        self.logger.error(f"Token issuance failed: {msg} (Code: {code})")
                        
                        # Set Cooldown if 429 or specific error code
                        # Code 5 often means "Limit Exceeded" in Kiwoom
                        if str(code) == "5" or "초과" in msg:
                            self._token_cooldown_until = datetime.now() + timedelta(minutes=10)
                            self.logger.warning(f"Rate Limit Hit. Cooldown set until {self._token_cooldown_until.strftime('%H:%M:%S')}")
                        
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
        interval: "day" (ka10081)
        """
        if interval == "day":
            endpoint = "/api/dostk/chart"
            tr_id = "ka10081"
        else:
            # Fallback or other intervals not fully supported yet
            endpoint = "/api/dostk/chart" 
            tr_id = "ka10081"

        # Params for ka10081
        base_dt = datetime.now().strftime("%Y%m%d")
        
        data = {
            "stk_cd": symbol,
            "base_dt": base_dt,
            "upd_stkpc_tp": "1" # Day
        }
        
        resp = await self.request("POST", endpoint, data=data, api_id=tr_id)
        
        if not resp:
            return None
            
        # Parse Response (ka10081)
        # Response: {"stk_dt_pole_chart_qry": [{"dt":..., "open_pric":...}, ...]}
        output = []
        items = resp.get("stk_dt_pole_chart_qry", [])
        
        for item in items:
            try:
                d = item["dt"]
                # Prices might have signs (+/-)
                o = abs(int(item["open_pric"]))
                h = abs(int(item["high_pric"]))
                l = abs(int(item["low_pric"]))
                c = abs(int(item["cur_prc"]))
                v = int(item["trde_qty"])
                
                output.append({
                    "date": d,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v
                })
            except Exception as e:
                self.logger.error(f"Error parsing item: {item} - {e}")
                
        # Return in format expected by BacktestDialog (resp["output"])
        return {"output": output, "rt_cd": resp.get("return_code", resp.get("rt_cd"))}

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
