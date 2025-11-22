import asyncio
import aiohttp
import json
import time
from collections import deque
from config import Config
from logger import logger
from typing import Optional, Dict, List
from datetime import datetime, timedelta

class KiwoomAPI:
    """
    Kiwoom REST API Implementation
    Supports both Real and Virtual (VTS) environments based on Config.IS_VIRTUAL
    """
    
    REAL_BASE_URL = "https://openapi.kiwoom.com"
    VIRTUAL_BASE_URL = "https://openapivts.kiwoom.com"
    
    def __init__(self):
        self.base_url = self.VIRTUAL_BASE_URL if Config.IS_VIRTUAL else self.REAL_BASE_URL
        self.app_key = Config.APP_KEY
        self.secret_key = Config.SECRET_KEY
        self.account_no = Config.ACCOUNT_NO
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate Limiting
        self.request_queue = asyncio.Queue()
        self.last_request_time = 0
        self.rate_limit_delay = 0.2 # 5 requests per second
        
        # WebSocket
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.approval_key: Optional[str] = None
        self.on_realtime_data = None
        
        logger.info(f"KiwoomAPI Initialized (Virtual: {Config.IS_VIRTUAL})")

    async def start(self):
        self.session = aiohttp.ClientSession()
        # Re-check config in case it changed (e.g. settings update)
        self.base_url = self.VIRTUAL_BASE_URL if Config.IS_VIRTUAL else self.REAL_BASE_URL
        self.app_key = Config.APP_KEY
        self.secret_key = Config.SECRET_KEY
        self.account_no = Config.ACCOUNT_NO
        
        if self.app_key and self.secret_key:
            await self.authenticate()
        else:
            logger.warning("APP_KEY or SECRET_KEY missing. Login skipped.")
            
        asyncio.create_task(self._process_queue())

    async def close(self):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self.session and not self.session.closed:
            await self.session.close()

    # ==================== Authentication ====================

    async def authenticate(self) -> bool:
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            payload = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.secret_key
            }
            
            async with self.session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Auth Failed ({resp.status}): {error_text}")
                    return False
                
                data = await resp.json()
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 86400)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Auth Success. Expires: {self.token_expires_at}")
                return True
        except Exception as e:
            logger.error(f"Auth Error: {e}")
            return False

    async def _ensure_token_valid(self):
        if not self.access_token or not self.token_expires_at:
            await self.authenticate()
        elif datetime.now() >= self.token_expires_at - timedelta(minutes=10):
            logger.info("Token expiring soon, refreshing...")
            await self.authenticate()

    def _get_headers(self, tr_id: str = "") -> Dict[str, str]:
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.secret_key,
            "custtype": "P",
        }
        if tr_id:
            headers["tr_id"] = tr_id
        return headers

    # ==================== Rate Limiting ====================

    async def _process_queue(self):
        while True:
            req_func, future = await self.request_queue.get()
            
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
            
            try:
                result = await req_func()
                if not future.done():
                    future.set_result(result)
            except Exception as e:
                logger.error(f"Request Error: {e}")
                if not future.done():
                    future.set_exception(e)
            finally:
                self.last_request_time = time.time()
                self.request_queue.task_done()

    async def _enqueue_request(self, func):
        future = asyncio.get_event_loop().create_future()
        await self.request_queue.put((func, future))
        return await future

    # ==================== Market Data ====================

    async def get_price(self, code):
        async def _req():
            await self._ensure_token_valid()
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = self._get_headers("FHKST01010100")
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    raise Exception(await resp.text())
                
                data = await resp.json()
                output = data.get("output", {})
                return {
                    "code": code,
                    "name": output.get("hts_kor_isnm", ""),
                    "price": int(output.get("stck_prpr", 0)),
                    "change": float(output.get("prdy_ctrt", 0)),
                    "volume": int(output.get("acml_vol", 0))
                }
        return await self._enqueue_request(_req)

    # ==================== Account & Trading ====================

    async def get_accounts(self) -> List[str]:
        """
        Fetches available account numbers.
        Note: Kiwoom REST API doesn't have a direct 'list accounts' endpoint like Open API (OCX).
        Usually, the user must input their account number.
        However, we can try to validate the configured account or return a list if stored.
        For now, we return the configured account if valid.
        """
        # In a real scenario with REST API, account numbers are usually managed by the client 
        # or retrieved via a specific endpoint if available (often not available in simple REST).
        # We will return the one from settings.
        if self.account_no:
            return [self.account_no]
        return []

    async def get_account_balance(self):
        async def _req():
            await self._ensure_token_valid()
            # VTTC8434R (Virtual) / TTTC8434R (Real)
            tr_id = "VTTC8434R" if Config.IS_VIRTUAL else "TTTC8434R"
            
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            headers = self._get_headers(tr_id)
            
            # Ensure account number is set
            acc_no = self.account_no or Config.ACCOUNT_NO
            if not acc_no:
                raise Exception("Account Number not set")

            params = {
                "CANO": acc_no,
                "ACNT_PRDT_CD": "01",
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    raise Exception(await resp.text())
                
                data = await resp.json()
                output1 = data.get("output1", [])
                output2 = data.get("output2", [{}])[0]
                
                stocks = []
                for item in output1:
                    stocks.append({
                        "code": item.get("pdno", ""),
                        "name": item.get("prdt_name", ""),
                        "qty": int(item.get("hldg_qty", 0)),
                        "avg_price": float(item.get("pchs_avg_pric", 0)),
                        "current_price": float(item.get("prpr", 0)),
                        "profit_pct": float(item.get("evlu_pfls_rt", 0))
                    })
                
                return {
                    "account_no": acc_no,
                    "total_asset": int(output2.get("tot_evlu_amt", 0)),
                    "cash": int(output2.get("prvs_rcdl_excc_amt", 0)),
                    "stocks": stocks
                }
        return await self._enqueue_request(_req)

    async def send_order(self, type, code, qty, price=0):
        # type: "BUY", "SELL"
        async def _req():
            await self._ensure_token_valid()
            
            is_buy = type == "BUY"
            # VTTC0802U/VTTC0801U (Virtual) or TTTC0802U/TTTC0801U (Real)
            tr_id_suffix = "0802U" if is_buy else "0801U"
            tr_id_prefix = "VTTC" if Config.IS_VIRTUAL else "TTTC"
            tr_id = f"{tr_id_prefix}{tr_id_suffix}"
            
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            headers = self._get_headers(tr_id)
            
            payload = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": "01",
                "PDNO": code,
                "ORD_DVSN": "00" if price > 0 else "01", # 00: Limit, 01: Market
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price) if price > 0 else "0"
            }
            
            async with self.session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(await resp.text())
                
                data = await resp.json()
                if data.get("rt_cd") != "0":
                     raise Exception(data.get("msg1"))
                     
                return {
                    "order_no": data.get("output", {}).get("ORD_NO"),
                    "status": "SUCCESS"
                }
        return await self._enqueue_request(_req)

    # ==================== WebSocket ====================

    async def connect_websocket(self, codes):
        try:
            # Real: ws://ops.kiwoom.com:21000, Virtual: ws://ops.kiwoom.com:31000
            port = 31000 if Config.IS_VIRTUAL else 21000
            ws_url = f"ws://ops.kiwoom.com:{port}"
            
            self.ws = await self.session.ws_connect(ws_url)
            logger.info(f"WebSocket Connected: {ws_url}")
            
            await self._get_approval_key()
            
            for code in codes:
                await self._subscribe_stock(code)
                
            asyncio.create_task(self._ws_message_handler())
        except Exception as e:
            logger.error(f"WebSocket Connection Failed: {e}")

    async def _get_approval_key(self):
        url = f"{self.base_url}/oauth2/approval"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }
        async with self.session.post(url, json=payload) as resp:
            data = await resp.json()
            self.approval_key = data.get("approval_key")
            logger.info(f"Approval Key Issued")

    async def _subscribe_stock(self, code):
        if not self.ws or not self.approval_key: return
        
        msg = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": code
                }
            }
        }
        await self.ws.send_json(msg)

    async def _ws_message_handler(self):
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Kiwoom WS sends raw text data, parsing needed
                    # Simplified for now, assuming JSON or structured text
                    # Real implementation needs detailed parsing based on Kiwoom docs
                    if self.on_realtime_data:
                        # Placeholder: In real usage, parse the '|' separated string
                        logger.debug(f"WS Data: {msg.data[:100]}...")
                        pass 
        except Exception as e:
            logger.error(f"WS Handler Error: {e}")
