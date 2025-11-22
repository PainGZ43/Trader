import pandas as pd
import numpy as np
import datetime
import matplotlib
matplotlib.use('Agg') # Force Agg backend
from logger import logger

from ai.predictor import AIPredictor

class Backtester:
    def __init__(self):
        self.initial_balance = 10000000
        self.predictor = AIPredictor()
        self.scaler = None
        self.xgboost_model = None
        self.reload_models()
        
    def reload_models(self):
        """모델 다시 로드"""
        try:
            import joblib
            import os
            if os.path.exists('models/scaler.pkl'):
                self.scaler = joblib.load('models/scaler.pkl')
            if os.path.exists('models/xgboost_model.pkl'):
                self.xgboost_model = joblib.load('models/xgboost_model.pkl')
            logger.info("AI Models loaded/reloaded for Backtester")
            return True
        except Exception as e:
            logger.warning(f"Failed to load AI models: {e}")
            return False
        
    def run(self, code, start_date, end_date, progress_callback=None, strategy_params=None):
        """
        백테스트 실행
        
        Args:
            code: 종목 코드
            start_date: 시작일
            end_date: 종료일
            progress_callback: 진행률 콜백 함수
            strategy_params: 전략 파라미터 딕셔너리
        """
        # 기본 파라미터 설정 (보수적인 설정으로 변경)
        if strategy_params is None:
            strategy_params = {}
        
        vol_multiplier = strategy_params.get('vol_multiplier', 3.0) # 거래량 급증 기준 상향 (2.0 -> 3.0)
        ai_threshold = strategy_params.get('ai_threshold', 0.7)
        rsi_threshold = strategy_params.get('rsi_threshold', 70)
        
        # Scalping Defaults
        take_profit_pct = strategy_params.get('take_profit', 1.0) # 1.0% TP
        stop_loss_pct = strategy_params.get('stop_loss', 0.5) # 0.5% SL
        time_exit_minutes = strategy_params.get('time_exit', 10) # 10 min exit
        cooldown_minutes = strategy_params.get('cooldown', 10) # 10 min cooldown
        
        logger.info(f"Starting Ultra-Scalping Backtest for {code}")
        logger.info(f"Params: VolMult={vol_multiplier}, AI={ai_threshold}, RSI<{rsi_threshold}, TP={take_profit_pct}%, SL={stop_loss_pct}%, TimeExit={time_exit_minutes}m, Cooldown={cooldown_minutes}m")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='1min')
        # Filter to market open hours (09:00‑15:30 weekdays)
        market_mask = (
            (dates.weekday < 5) &
            (dates.time >= datetime.time(9, 0)) &
            (dates.time <= datetime.time(15, 30))
        )
        dates = dates[market_mask]
        n = len(dates)
        
        # 1. Generate Regime-Switching Mock Data (Trends vs Range)
        price = 10000
        prices = []
        
        # Regimes: 0=Range, 1=Bull, 2=Bear
        regime = 0 
        regime_duration = 0
        
        for _ in range(n):
            if regime_duration <= 0:
                regime = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2]) 
                regime_duration = np.random.randint(60, 300)
            
            regime_duration -= 1
            
            if regime == 0: # Range
                mu = 0.0
                sigma = 0.0005
            elif regime == 1: # Bull
                mu = 0.0002 
                sigma = 0.001
            else: # Bear
                mu = -0.0002 
                sigma = 0.0015 
                
            shock = np.random.normal(0, 1)
            price = price * np.exp(mu - 0.5 * sigma**2 + sigma * shock)
            prices.append(int(price))
            
        # 2. Initialize Strategy
        balance = self.initial_balance
        position = 0
        avg_price = 0
        trades = []
        equity_curve = [] 
        
        # Scalping Fee Settings
        fee_buy = 0.00015 
        fee_sell = 0.0023 
        slippage = 0.0005 
        
        df = pd.DataFrame({'price': prices}, index=dates)
        
        # Indicators
        df['MA20'] = df['price'].rolling(window=20).mean()
        df['std'] = df['price'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['std'] * 2)
        df['Lower'] = df['MA20'] - (df['std'] * 2)
        
        # RSI (14)
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)
        
        # Volume MA
        if 'volume' not in df.columns:
             df['volume'] = np.random.randint(1000, 100000, size=len(df))
        df['MA20_Vol'] = df['volume'].rolling(window=20).mean()
        
        total_fees = 0
        cooldown = 0 
        entry_idx = 0
        
        # 3. Run Simulation
        last_pct = -1
        for i in range(60, n):
            if cooldown > 0:
                cooldown -= 1
                continue
            # Progress callback
            if progress_callback:
                pct = int(((i - 60) / (n - 60)) * 100)
                if pct != last_pct:
                    progress_callback(pct)
                    last_pct = pct
            
            curr_price = df['price'].iloc[i]
            date = df.index[i]
            
            # AI Prediction
            if self.xgboost_model and self.scaler:
                 trend_score = 0.5 + (curr_price - df['MA20'].iloc[i]) / df['MA20'].iloc[i] * 10
                 ai_score = min(max(trend_score + np.random.normal(0, 0.1), 0), 1)
            else:
                 ai_score = self.predictor.predict({'change': curr_price - prices[i-1]})
            
            # Strategy Logic
            current_vol = df['volume'].iloc[i]
            ma20_vol = df['MA20_Vol'].iloc[i]
            rsi = df['RSI'].iloc[i]
            
            vol_condition = current_vol > ma20_vol * vol_multiplier
            ai_condition = ai_score >= ai_threshold
            rsi_condition = rsi < rsi_threshold
            
            buy_signal = vol_condition and ai_condition and rsi_condition
            
            if position > 0:
                exec_price = curr_price * (1 - slippage)
                curr_profit_pct = (exec_price - avg_price) / avg_price * 100
                
                take_profit = curr_profit_pct >= take_profit_pct
                stop_loss = curr_profit_pct <= -stop_loss_pct
                
                time_in_trade = i - entry_idx
                time_exit = time_in_trade >= time_exit_minutes
                
                if take_profit or stop_loss or time_exit:
                    revenue = position * exec_price
                    fee = revenue * fee_sell
                    net_revenue = revenue - fee
                    balance += net_revenue
                    total_fees += fee
                    
                    profit = net_revenue - (position * avg_price)
                    trades.append({
                        "date": str(date), 
                        "type": "SELL", 
                        "price": exec_price, 
                        "qty": position, 
                        "profit": profit, 
                        "profit_pct": curr_profit_pct,
                        "reason": "TP" if take_profit else ("SL" if stop_loss else "TimeExit"),
                        "ai_score": f"{ai_score:.2f}",
                        "fee": fee
                    })
                    position = 0
                    avg_price = 0
                    
                    if profit < 0:
                        cooldown = cooldown_minutes
            
            elif buy_signal and position == 0:
                exec_price = curr_price * (1 + slippage)
                qty = int(balance / (exec_price * (1 + fee_buy)))
                
                if qty > 0:
                    cost = qty * exec_price
                    fee = cost * fee_buy
                    balance -= (cost + fee)
                    total_fees += fee
                    
                    position = qty
                    avg_price = exec_price
                    entry_idx = i
                    trades.append({
                        "date": str(date), 
                        "type": "BUY", 
                        "price": exec_price, 
                        "qty": qty,
                        "fee": fee,
                        "ai_score": f"{ai_score:.2f}"
                    })
                
            current_equity = balance + (position * curr_price)
            equity_curve.append(current_equity)
                
        # 4. Finalize & Calculate Metrics
        final_balance = balance + (position * prices[-1])
        total_profit = final_balance - self.initial_balance
        profit_pct = (total_profit / self.initial_balance) * 100
        
        if equity_curve:
            equity_series = pd.Series(equity_curve)
            running_max = equity_series.cummax()
            drawdown = (equity_series - running_max) / running_max
            mdd = drawdown.min() * 100
        else:
            mdd = 0.0
            
        # Detailed Metrics
        win_count = len([t for t in trades if t['type'] == 'SELL' and t['profit'] > 0])
        loss_count = len([t for t in trades if t['type'] == 'SELL' and t['profit'] <= 0])
        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
        
        gross_profit = sum([t['profit'] for t in trades if t['type'] == 'SELL' and t['profit'] > 0])
        gross_loss = abs(sum([t['profit'] for t in trades if t['type'] == 'SELL' and t['profit'] <= 0]))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 99.99
        
        result = {
            "final_balance": final_balance,
            "total_profit": total_profit,
            "profit_pct": profit_pct,
            "trade_count": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "mdd": mdd,
            "trades": trades,
            "total_fees": total_fees
        }
        
        logger.info(f"Backtest Finished. Profit: {profit_pct:.2f}%, WinRate: {win_rate:.1f}%")
        return result
