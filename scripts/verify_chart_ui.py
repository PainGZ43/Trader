import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer
from qasync import QEventLoop
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.dashboard import Dashboard
from data.indicator_engine import indicator_engine

def create_mock_data(length=200):
    """Generate mock OHLCV data with a trend."""
    dates = [datetime.now() - timedelta(minutes=length-i) for i in range(length)]
    
    close = 1000.0
    data = []
    
    for d in dates:
        change = np.random.normal(0, 2)
        close += change
        high = close + abs(np.random.normal(0, 1))
        low = close - abs(np.random.normal(0, 1))
        open_p = close + np.random.normal(0, 1)
        volume = int(abs(np.random.normal(100, 50)))
        
        data.append({
            "timestamp": d,
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
        
    return pd.DataFrame(data)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chart Verification")
        self.resize(1200, 800)
        
        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)
        
        # Load Initial Data
        print("Generating Mock Data...")
        self.df = create_mock_data(200)
        
        # Calculate Indicators
        print("Calculating Indicators...")
        self.df = indicator_engine.add_indicators(self.df)
        print("Columns:", self.df.columns)
        
        # Set to Dashboard
        # We manually set data to avoid async call in __init__ for this test
        self.dashboard.current_symbol = "TEST"
        self.dashboard.stack_layout.setCurrentIndex(1)
        self.dashboard.history_data = self.df
        self.dashboard.pending_chart_data = self.df
        
        # Simulate Real-time Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tick)
        self.timer.start(100) # 100ms
        
        self.current_price = self.df.iloc[-1]['close']

    def update_tick(self):
        # Random Walk
        change = np.random.normal(0, 1)
        self.current_price += change
        
        tick_data = {
            "type": "REALTIME",
            "code": "TEST",
            "price": self.current_price,
            "volume": 10
        }
        
        self.dashboard.process_data(tick_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = TestWindow()
    window.show()
    
    print("Running Visual Test... Close window to finish.")
    with loop:
        loop.run_forever()
