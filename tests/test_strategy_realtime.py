import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from strategy.strategies import VolatilityBreakoutStrategy, RSIStrategy
from strategy.base_strategy import Signal

class TestStrategyRealtime(unittest.IsolatedAsyncioTestCase):
    
    async def test_volatility_breakout_realtime(self):
        """Test Volatility Breakout Real-time Logic"""
        strategy = VolatilityBreakoutStrategy("VB_TEST", "005930")
        strategy.initialize({"k": 0.5})
        
        # 1. Warm-up with Daily Data (Prev Range)
        # Prev High: 1000, Prev Low: 900, Close: 950 -> Range = 100
        df = pd.DataFrame({
            'high': [1000], 'low': [900], 'close': [950], 'open': [900], 'volume': [1000]
        })
        strategy.update_market_data(df)
        
        self.assertEqual(strategy.prev_range, 100)
        
        # 2. Real-time Data (Open: 950)
        # Target = 950 + (100 * 0.5) = 1000
        
        # Case A: Price < Target (990) -> No Signal
        data_a = {'price': 990, 'open': 950}
        signal = await strategy.on_realtime_data(data_a)
        self.assertIsNone(signal)
        
        # Case B: Price > Target (1010) -> BUY Signal
        data_b = {'price': 1010, 'open': 950}
        signal = await strategy.on_realtime_data(data_b)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, 'BUY')
        self.assertEqual(signal.price, 1010)

    async def test_rsi_realtime(self):
        """Test RSI Real-time Logic"""
        strategy = RSIStrategy("RSI_TEST", "005930")
        strategy.initialize({"period": 14, "buy_threshold": 30, "sell_threshold": 70})
        
        # 1. Warm-up with 20 data points
        # Create a downtrend to lower RSI
        prices = [100 - i for i in range(20)] # 100, 99, ..., 81
        df = pd.DataFrame({'close': prices})
        strategy.update_market_data(df)
        
        self.assertEqual(len(strategy.prices), 20)
        
        # 2. Real-time Data (Continue downtrend)
        # Price 80 -> RSI should be low
        data = {'price': 80}
        signal = await strategy.on_realtime_data(data)
        
        # Since it's a straight downtrend, RSI should be 0 or very low -> BUY
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, 'BUY')
        self.assertEqual(signal.price, 80)
        
        # 3. Simulate Uptrend to trigger SELL
        # We need to push many prices to raise RSI
        # Reset strategy for clean test or just push many
        strategy.state.current_position = 1 # Assume we bought
        
        # Push prices up
        for p in range(80, 150, 2):
            await strategy.on_realtime_data({'price': p})
            
        # Check last signal (should be SELL eventually)
        # But on_realtime_data returns signal only on the tick it crosses.
        # Let's just check if we get a SELL signal on a high price
        signal = await strategy.on_realtime_data({'price': 200})
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, 'SELL')

if __name__ == "__main__":
    unittest.main()
