from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.order_book_widget import OrderBookWidget
import pandas as pd
from core.language import language_manager

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
        # self.order_book_widget.setFixedWidth(300) # REMOVED fixed width
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
        
        if event_type == "REALTIME":
            # Switch to Active View if on Welcome Screen
            if self.stack_layout.currentIndex() == 0:
                self.stack_layout.setCurrentIndex(1)
                
            # Queue for chart update
            # Assuming data contains candle info or tick info that we aggregate
            # For now, let's assume we get a full candle or tick
            pass 
            
        elif event_type == "ORDERBOOK":
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
            
        # Chart update logic would go here (e.g. appending new candle)
        # For demo, we can generate dummy data if needed

