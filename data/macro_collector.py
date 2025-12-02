import asyncio
import aiohttp
from core.logger import get_logger
from data.kiwoom_rest_client import kiwoom_client
from core.event_bus import event_bus
from data.websocket_client import ws_client

class MacroCollector:
    """
    Collects Macroeconomic Data:
    - Market Indices (KOSPI)
    - Exchange Rates (USD/KRW)
    """
    def __init__(self):
        self.logger = get_logger("MacroCollector")
        self.rest_client = kiwoom_client
        self.ws_client = ws_client
        self.indices = {
            "KOSPI": 0.0
        }
        self.changes = {} 
        self.exchange_rate = 0.0

    async def subscribe_indices(self):
        """
        Subscribe to Real-time Index Data (JISU).
        """
        self.logger.info("Subscribing to Real-time Indices...")
        # KOSPI (001)
        await self.ws_client.subscribe("JISU", "001")

    async def update_market_indices(self):
        """
        Fetch KOSPI & KOSDAQ indices.
        Primary: Naver Finance (Web Scraping)
        Secondary: Kiwoom API (Fallback)
        """
        targets = [
            ("KOSPI", "001"),
            ("KOSDAQ", "201") # Kiwoom code for KOSDAQ is usually 101 or 201 depending on market type param
        ]
        
        for name, kiwoom_code in targets:
            # 1. Try Naver Finance
            try:
                url = f"https://finance.naver.com/sise/sise_index.naver?code={name}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            text = await response.text()
                            
                            # Parse Price
                            if 'id="now_value"' in text:
                                start_idx = text.find('id="now_value"')
                                val_start = text.find('>', start_idx) + 1
                                val_end = text.find('<', val_start)
                                val_str = text[val_start:val_end].replace(",", "")
                                self.indices[name] = float(val_str)
                                
                                # Parse Change
                                if 'id="change_value_and_rate"' in text:
                                    c_start = text.find('id="change_value_and_rate"')
                                    
                                    # Find inner span for Amount
                                    amt_start_tag = text.find('<span>', c_start)
                                    if amt_start_tag != -1:
                                        amt_start = amt_start_tag + 6
                                        amt_end = text.find('</span>', amt_start)
                                        change_amt = text[amt_start:amt_end].strip()
                                        
                                        # Find Percent
                                        pct_start = amt_end + 7
                                        pct_end = text.find('<', pct_start)
                                        change_pct = text[pct_start:pct_end].strip().replace("%", "")
                                        
                                        # Determine Sign
                                        sign = ""
                                        if "+" in change_pct: sign = "+"
                                        elif "-" in change_pct: sign = "-"
                                        else:
                                            if "point_dn" in text[c_start-100:c_start+100]: sign = "-"
                                            elif "point_up" in text[c_start-100:c_start+100]: sign = "+"
                                        
                                        # Clean
                                        change_amt = change_amt.replace("+", "").replace("-", "")
                                        change_pct = change_pct.replace("+", "").replace("-", "")
                                        
                                        self.changes[name] = f"{sign}{change_amt} ({sign}{change_pct}%)"
                                
                                self.logger.info(f"Updated {name} (via Naver): {self.indices[name]} {self.changes.get(name, '')}")
                                continue # Success, skip fallback

            except Exception as e:
                self.logger.warning(f"Naver {name} scraping failed: {e}")

            # 2. Fallback: Kiwoom API
            try:
                # Kiwoom Market Codes: 0=KOSPI, 10=KOSDAQ (for code list), but for mrkcond:
                # mrkt_tp: 1=KOSPI, 2=KOSDAQ
                mrkt_tp = "1" if name == "KOSPI" else "2"
                
                # We need to use get_market_index with correct code
                # My existing get_market_index takes "001" or "200" (KOSDAQ is usually 201 or similar in TR)
                # Let's assume get_market_index handles "001" -> KOSPI, "201" -> KOSDAQ logic internally or we pass mapped code.
                # In kiwoom_rest_client.py:
                # if market_code == "001": mrkt_tp = "1"
                # elif market_code == "200": mrkt_tp = "2"
                
                k_code = "001" if name == "KOSPI" else "200" # Using 200 for KOSDAQ based on client logic
                
                data = await self.rest_client.get_market_index(k_code)
                if data:
                    price = 0.0
                    if "inds_netprps" in data:
                        items = data["inds_netprps"]
                        if items:
                            price_str = items[0].get("cur_prc", "0")
                            price = float(price_str.replace(",", "").replace("+", ""))
                            
                            c_amt = items[0].get("prc_change", "0")
                            c_rate = items[0].get("prc_change_rate", "0")
                            self.changes[name] = f"{c_amt} ({c_rate}%)"
                    
                    elif "output" in data:
                        price = float(str(data.get("output", {}).get("price", "0")).replace(",", ""))
                    
                    if price > 0:
                        self.indices[name] = price
                        self.logger.info(f"Updated {name} (via Kiwoom): {price}")
                        
            except Exception as e:
                self.logger.error(f"Failed to update {name} via Kiwoom: {e}")

    async def update_exchange_rate(self):
        """
        Fetch USD/KRW exchange rate.
        Primary: Naver Finance (Web Scraping)
        Secondary: Kiwoom KODEX USD Futures ETF (Proxy)
        """
        # 1. Try Naver Finance
        try:
            url = "https://finance.naver.com/marketindex/"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        
                        # Find the container for exchange rate
                        if "exchangeList" in text:
                            start_idx = text.find('<div class="head_info point_dn">') 
                            is_down = True
                            if start_idx == -1:
                                start_idx = text.find('<div class="head_info point_up">')
                                is_down = False
                            
                            if start_idx != -1:
                                # Value
                                value_start = text.find('<span class="value">', start_idx)
                                if value_start != -1:
                                    value_end = text.find('</span>', value_start)
                                    value_str = text[value_start+20:value_end].replace(",", "")
                                    self.exchange_rate = float(value_str)
                                    
                                    # Change Amount
                                    change_start = text.find('<span class="change">', start_idx)
                                    change_end = text.find('</span>', change_start)
                                    change_amt_str = text[change_start+21:change_end].strip()
                                    
                                    # Calculate Percentage
                                    try:
                                        change_val = float(change_amt_str.replace(",", ""))
                                        if is_down:
                                            change_val = -change_val
                                            
                                        prev_close = self.exchange_rate - change_val
                                        if prev_close != 0:
                                            pct = (change_val / prev_close) * 100
                                            sign = "+" if pct > 0 else ""
                                            self.changes["USD/KRW"] = f"{sign}{change_val} ({sign}{pct:.2f}%)"
                                        else:
                                            self.changes["USD/KRW"] = f"{change_val}"
                                    except:
                                        # Fallback if calc fails
                                        sign = "-" if is_down else "+"
                                        self.changes["USD/KRW"] = f"{sign}{change_amt_str}"
                                    
                                    self.logger.info(f"Updated USD/KRW (via Naver): {self.exchange_rate} {self.changes.get('USD/KRW')}")
                                    return

        except Exception as e:
            self.logger.warning(f"Naver Finance scraping failed: {e}")

        # 2. Fallback: Kiwoom ETF
        try:
            # KODEX USD Futures (261240)
            data = await self.rest_client.get_current_price("261240")
            
            price = 0.0
            
            if data and "output" in data:
                price_str = data["output"].get("price", "0")
                price = float(price_str.replace(",", ""))
            
            elif data and ("buy_fpr_bid" in data or "sel_fpr_bid" in data):
                price_str = data.get("buy_fpr_bid", "0")
                if price_str == "0" or not price_str:
                     price_str = data.get("sel_fpr_bid", "0")
                
                clean_str = price_str.replace(",", "").replace("+", "").replace("-", "")
                if clean_str:
                    price = float(clean_str)

            if price > 0:
                self.exchange_rate = price / 10.0
                self.logger.info(f"Updated USD/KRW (via Kiwoom ETF): {self.exchange_rate}")
            else:
                self.logger.warning(f"Kiwoom returned 0 price for USD Futures ETF.")
                
        except Exception as e:
            self.logger.error(f"Exchange rate update error: {e}")

    async def on_realtime_data(self, data):
        """
        Handle Real-time Data from WebSocket.
        """
        msg_type = data.get("type")
        if msg_type == "JISU":
            code = data.get("code")
            price = float(data.get("price", 0))
            change_pct = data.get("change_pct", "0.0%")
            
            name = None
            if code == "001":
                name = "KOSPI"
            
            if name:
                self.indices[name] = price
                self.changes[name] = change_pct
                
                # Publish Event Immediately
                event_data = {
                    "indices": self.indices,
                    "changes": self.changes,
                    "exchange_rate": self.exchange_rate
                }
                event_bus.publish("market.data.macro", event_data)

    async def start_scheduler(self):
        """
        Periodically update macro data.
        """
        self.logger.info("Starting MacroCollector Scheduler...")
        
        # Initial Subscription
        await self.subscribe_indices()
        
        while True:
            await self.update_market_indices()
            await self.update_exchange_rate()
            
            # Publish Event (Periodic)
            event_data = {
                "indices": self.indices,
                "changes": self.changes,
                "exchange_rate": self.exchange_rate
            }
            event_bus.publish("market.data.macro", event_data)
            
            await asyncio.sleep(10) # 10s polling for backup

macro_collector = MacroCollector()
