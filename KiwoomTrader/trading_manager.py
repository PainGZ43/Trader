import asyncio
from datetime import datetime
from config import Config
from logger import logger
from database import get_db, TradeLog
from kiwoom_api import KiwoomAPI
from notifier import Notifier
from ai.sentiment import SentimentAnalyzer

class TradingManager:
    def __init__(self):
        self.api = KiwoomAPI()
        self.notifier = Notifier()
        self.db = get_db()
        self.sentiment = SentimentAnalyzer()
        self.is_running = False
        self.is_virtual = Config.IS_VIRTUAL
        
        # Portfolio State (In-Memory for Simulation / Cache for Real)
        self.portfolio = {} # {code: {qty, avg_price, name}}
        self.balance = 10000000 # Initial Mock Balance
        self.total_assets = 10000000
        
        # Risk Management
        self.daily_loss_limit = 0.03 # -3%
        self.start_balance = 0
        
    async def start(self):
        await self.api.start()
        self.is_running = True
        logger.info("Trading Manager Started")
        self.notifier.send("Trading System Started")
        
        # Load initial account info
        acc = await self.api.get_account_balance()
        if Config.IS_VIRTUAL:
             logger.info(f"[SIMULATION] Initial Balance: {self.balance}")
             self.start_balance = self.balance
        else:
            # Parse real account info
            pass

    async def stop(self):
        self.is_running = False
        await self.api.close()
        logger.info("Trading Manager Stopped")
        self.notifier.send("Trading System Stopped")

    async def analyze_market_sentiment(self, code):
        """
        Analyzes sentiment for a stock and returns a score.
        """
        try:
            score = await self.sentiment.get_sentiment_score(code)
            logger.info(f"Sentiment Score for {code}: {score}")
            return score
        except Exception as e:
            logger.error(f"Sentiment Analysis Failed: {e}")
            return 0.0

    async def buy(self, code, qty, price, reason="Strategy"):
        if not self.is_running: return

        # 0. Sentiment Check (Optional Filter)
        sentiment_score = await self.analyze_market_sentiment(code)
        if sentiment_score < -0.5:
            logger.warning(f"Skipping BUY {code} due to negative sentiment: {sentiment_score}")
            return

        # 1. Check Balance
        cost = qty * price
        if self.balance < cost:
            logger.warning(f"Insufficient Balance for BUY {code}: Need {cost}, Have {self.balance}")
            return
            
        # 2. Send Order
        res = await self.api.send_order("BUY", code, qty, price)
        
        # 3. Update Portfolio (Simulation Logic)
        if res and Config.IS_VIRTUAL:
            self.balance -= cost
            if code not in self.portfolio:
                self.portfolio[code] = {'qty': 0, 'avg_price': 0, 'name': 'Unknown'}
            
            # Update Avg Price
            old_qty = self.portfolio[code]['qty']
            old_cost = old_qty * self.portfolio[code]['avg_price']
            new_cost = old_cost + cost
            new_qty = old_qty + qty
            
            self.portfolio[code]['qty'] = new_qty
            self.portfolio[code]['avg_price'] = new_cost / new_qty
            
            self._log_trade(code, "BUY", price, qty, f"{reason} (Sent:{sentiment_score:.2f})")
            self.notifier.send(f"BUY {code} {qty}ea @ {price:,} (Reason: {reason}, Sent: {sentiment_score:.2f})")
            self._update_assets()

    async def sell(self, code, qty, price, reason="Strategy"):
        if not self.is_running: return

        if code not in self.portfolio or self.portfolio[code]['qty'] < qty:
            logger.warning(f"Not enough quantity to sell {code}")
            return
            
        res = await self.api.send_order("SELL", code, qty, price)
        
        if res and Config.IS_VIRTUAL:
            revenue = qty * price
            self.balance += revenue
            
            # Calculate Profit
            avg_price = self.portfolio[code]['avg_price']
            profit = (price - avg_price) * qty
            profit_pct = (price - avg_price) / avg_price * 100
            
            self.portfolio[code]['qty'] -= qty
            if self.portfolio[code]['qty'] == 0:
                del self.portfolio[code]
                
            self._log_trade(code, "SELL", price, qty, reason, profit_pct)
            self.notifier.send(f"SELL {code} {qty}ea @ {price:,} (Profit: {profit_pct:.2f}%)")
            self._update_assets()

    def _log_trade(self, code, side, price, qty, note, profit_pct=None):
        try:
            log = TradeLog(
                code=code,
                side=side,
                price=price,
                qty=qty,
                note=note,
                profit_pct=profit_pct
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"DB Log Error: {e}")

    def _update_assets(self):
        stock_val = sum([v['qty'] * v['avg_price'] for k, v in self.portfolio.items()]) # Using avg_price for estimation
        self.total_assets = self.balance + stock_val
        
        # Circuit Breaker Check
        if self.start_balance > 0:
            loss_pct = (self.total_assets - self.start_balance) / self.start_balance
            if loss_pct < -self.daily_loss_limit:
                logger.critical("Circuit Breaker Triggered! Stopping Trading.")
                self.notifier.send("[EMERGENCY] Circuit Breaker Triggered. Trading Stopped.")
                asyncio.create_task(self.stop())
