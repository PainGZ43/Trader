from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.order_book_widget import OrderBookWidget
import pandas as pd
from datetime import datetime
from core.language import language_manager
from data.indicator_engine import indicator_engine
from data.data_collector import data_collector
import asyncio

class Dashboard(QWidget):
    # Signal for thread-safe UI update
    data_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Connect signal
        self.data_received.connect(self.process_data)
        
        # Throttling Timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_ui)
        self.update_timer.start(100) # 100ms refresh rate
        
        self.pending_chart_data = None
        self.pending_orderbook_data = None
        
        self.current_symbol = None
        self.history_data = pd.DataFrame() # Stores OHLCV + Indicators

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Main Content (Stacked Layout)
        from PyQt6.QtWidgets import QStackedLayout
        self.stack_layout = QStackedLayout()
        
        # Page 0: Welcome / Empty State
        self.welcome_widget = QLabel(language_manager.get_text("msg_welcome_select_stock", "Select a stock to start trading."))
        self.welcome_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_widget.setStyleSheet("font-size: 24px; color: #666; font-weight: bold;")
        self.stack_layout.addWidget(self.welcome_widget)
        
        # Page 1: Active Dashboard (Splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Chart Area
        self.chart_widget = ChartWidget()
        splitter.addWidget(self.chart_widget)
        
        # Order Book Area
        self.order_book_widget = OrderBookWidget()
        splitter.addWidget(self.order_book_widget)
        
        splitter.setStretchFactor(0, 1) # Chart takes available space
        splitter.setStretchFactor(1, 0)
        
        # Wrap splitter in a widget to add to stack
        splitter_widget = QWidget()
        splitter_layout = QHBoxLayout(splitter_widget)
        splitter_layout.setContentsMargins(0,0,0,0)
        splitter_layout.addWidget(splitter)
        
        self.stack_layout.addWidget(splitter_widget)
        
        layout.addLayout(self.stack_layout)
        
        # Default to Welcome
        self.stack_layout.setCurrentIndex(0)

    def set_active_symbol(self, symbol):
        """
        Set the active symbol and load initial data.
        """
        self.current_symbol = symbol
        self.stack_layout.setCurrentIndex(1)
        
        # Clear previous data
        self.history_data = pd.DataFrame()
        self.chart_widget.update_chart(self.history_data)
        
        # Load initial data (Async task)
        asyncio.create_task(self._load_initial_data(symbol))

    async def _load_initial_data(self, symbol):
        """
        Fetch recent data from DataCollector (DB).
        """
        df = await data_collector.get_recent_data(symbol, limit=200)
        if not df.empty:
            # Calculate Indicators
            df = indicator_engine.add_indicators(df)
            self.history_data = df
            self.pending_chart_data = df # Trigger update

    def on_data_received(self, data):
        """
        Callback called by DataCollector (background thread).
        Emits signal to update UI on main thread.
        """
        self.data_received.emit(data)

    def process_data(self, data):
        """
        Slot to receive data and queue it for update.
        """
        event_type = data.get("type")
        symbol = data.get("code")
        
        if event_type == "REALTIME":
            if symbol != self.current_symbol:
                return

            # Update History Data
            price = float(data.get("price", 0))
            volume = int(data.get("volume", 0))
            timestamp = datetime.now().replace(second=0, microsecond=0)
            
            if self.history_data.empty:
                # Initialize if empty
                new_row = pd.DataFrame([{
                    "timestamp": timestamp,
                    "open": price, "high": price, "low": price, "close": price, "volume": volume
                }])
                self.history_data = new_row
            else:
                last_ts = self.history_data.iloc[-1]['timestamp']
                
                if timestamp > last_ts:
                    # New Candle
                    new_row = pd.DataFrame([{
                        "timestamp": timestamp,
                        "open": price, "high": price, "low": price, "close": price, "volume": volume
                    }])
                    self.history_data = pd.concat([self.history_data, new_row], ignore_index=True)
                else:
                    # Update Current Candle
                    idx = self.history_data.index[-1]
                    self.history_data.at[idx, 'high'] = max(self.history_data.at[idx, 'high'], price)
                    self.history_data.at[idx, 'low'] = min(self.history_data.at[idx, 'low'], price)
                    self.history_data.at[idx, 'close'] = price
                    self.history_data.at[idx, 'volume'] += volume 
            
            # Ensure Float for Indicators
            cols = ['open', 'high', 'low', 'close', 'volume']
            for c in cols:
                if c in self.history_data.columns:
                    self.history_data[c] = self.history_data[c].astype(float)

            # Recalculate Indicators (Optimize: only if needed or every N ticks?)
            # For now, calc every tick for smooth look
            try:
                self.history_data = indicator_engine.add_indicators(self.history_data)
                # print(f"Indicators Calculated. Columns: {len(self.history_data.columns)}") # Debug
            except Exception as e:
                print(f"Indicator Error: {e}")
            
            # Limit History Size (Keep last 1000 candles)
            if len(self.history_data) > 1000:
                self.history_data = self.history_data.iloc[-1000:].reset_index(drop=True)
            
            # Queue for chart update
            self.pending_chart_data = self.history_data
            
        elif event_type == "ORDERBOOK":
            if symbol == self.current_symbol:
                self.pending_orderbook_data = data

    def refresh_ui(self):
        """
        Called by timer to update widgets with latest pending data.
        """
        if self.pending_orderbook_data:
            asks = self.pending_orderbook_data.get("asks", [])
            bids = self.pending_orderbook_data.get("bids", [])
            self.order_book_widget.update_orderbook(asks, bids)
            self.pending_orderbook_data = None
            
        if self.pending_chart_data is not None:
            self.chart_widget.update_chart(self.pending_chart_data)
            self.pending_chart_data = None


