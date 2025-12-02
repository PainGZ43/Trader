import asyncio
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QFormLayout, QSplitter, QWidget, QMessageBox)
from PyQt6.QtCore import Qt, QDate
import pyqtgraph as pg
from qasync import asyncSlot

from strategy.backtester import EventDrivenBacktester
from strategy.strategies import VolatilityBreakoutStrategy, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandStrategy
from data.data_collector import data_collector
from core.logger import get_logger

class BacktestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backtest Lab")
        self.resize(1200, 800)
        self.logger = get_logger("BacktestUI")
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Control Panel
        control_group = QGroupBox("Configuration")
        control_layout = QHBoxLayout()
        
        # Strategy Selection
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItems([
            "VolatilityBreakoutStrategy", 
            "MovingAverageCrossoverStrategy", 
            "RSIStrategy", 
            "BollingerBandStrategy"
        ])
        control_layout.addWidget(QLabel("Strategy:"))
        control_layout.addWidget(self.combo_strategy)
        
        # Symbol
        from ui.widgets.symbol_search import SymbolSearchWidget
        self.txt_symbol = SymbolSearchWidget()
        control_layout.addWidget(QLabel("Symbol:"))
        control_layout.addWidget(self.txt_symbol)
        
        # Date Range
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setCalendarPopup(True)
        control_layout.addWidget(QLabel("Start:"))
        control_layout.addWidget(self.date_start)
        
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setCalendarPopup(True)
        control_layout.addWidget(QLabel("End:"))
        control_layout.addWidget(self.date_end)
        
        # Run Button
        self.btn_run = QPushButton("Run Backtest")
        self.btn_run.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_run.clicked.connect(self.run_backtest)
        control_layout.addWidget(self.btn_run)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Main Content (Splitter)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 1. Chart Area
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('#1e1e1e')
        self.chart_widget.setTitle("Equity Curve", color="w", size="12pt")
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        self.chart_widget.setLabel('left', 'Equity (KRW)')
        self.chart_widget.setLabel('bottom', 'Time')
        splitter.addWidget(self.chart_widget)
        
        # 2. Results Area (Metrics + Trade List)
        results_widget = QWidget()
        results_layout = QHBoxLayout(results_widget)
        
        # Metrics Table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)
        results_layout.addWidget(self.metrics_table, 1)
        
        # Trade List Table
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(5)
        self.trade_table.setHorizontalHeaderLabels(["Time", "Type", "Price", "Qty", "Profit"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trade_table.verticalHeader().setVisible(False)
        results_layout.addWidget(self.trade_table, 2)
        
        splitter.addWidget(results_widget)
        
        layout.addWidget(splitter)

    @asyncSlot()
    async def run_backtest(self):
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Running...")
        
        try:
            # 1. Get Parameters
            strategy_name = self.combo_strategy.currentText()
            symbol = self.txt_symbol.get_current_code()
            if not symbol:
                QMessageBox.warning(self, "Error", "Please select a valid symbol.")
                return
            start_date = self.date_start.date().toString("yyyyMMdd")
            end_date = self.date_end.date().toString("yyyyMMdd")
            
            # 2. Fetch Data (Using DataCollector logic or direct API)
            # We need daily data for backtest usually, or minute data
            # Let's try to fetch daily data from Kiwoom via DataCollector
            # Note: DataCollector.get_recent_data is for minute data from DB.
            # We need a way to fetch historical range.
            # Let's use kiwoom_client directly or add a method to DataCollector.
            # For now, use kiwoom_client.get_ohlcv
            
            from data.kiwoom_rest_client import kiwoom_client
            resp = await kiwoom_client.get_ohlcv(symbol, "day", start_date) # This API usually returns from today backwards?
            # Kiwoom API 'opt10081' (daily) takes 'date' as start date? No, it takes 'date' as end date usually or request date.
            # Actually opt10081 returns data ending at 'date'. To get range, we might need multiple calls or just get enough data.
            # For simplicity, let's assume we get 500 days ending today.
            
            if not resp or "output" not in resp:
                QMessageBox.warning(self, "Error", "Failed to fetch data.")
                return

            # Parse Data
            data_list = []
            for item in resp["output"]:
                d = item["date"]
                if d < start_date: continue # Filter
                if d > end_date: continue
                
                data_list.append({
                    "timestamp": datetime.strptime(d, "%Y%m%d"),
                    "open": int(item["open"]),
                    "high": int(item["high"]),
                    "low": int(item["low"]),
                    "close": int(item["close"]),
                    "volume": int(item["volume"])
                })
            
            # Sort by date asc
            data_list.sort(key=lambda x: x["timestamp"])
            df = pd.DataFrame(data_list)
            df.set_index("timestamp", inplace=True)
            
            if df.empty:
                QMessageBox.warning(self, "Error", "No data found for the selected range.")
                return

            # 3. Initialize Strategy
            if strategy_name == "VolatilityBreakoutStrategy":
                strategy = VolatilityBreakoutStrategy("BT_VB", symbol)
            elif strategy_name == "MovingAverageCrossoverStrategy":
                strategy = MovingAverageCrossoverStrategy("BT_MA", symbol)
            elif strategy_name == "RSIStrategy":
                strategy = RSIStrategy("BT_RSI", symbol)
            elif strategy_name == "BollingerBandStrategy":
                strategy = BollingerBandStrategy("BT_BB", symbol)
            else:
                return
                
            # Load default config (TODO: Allow editing config in UI)
            strategy.initialize({}) 
            
            # 4. Run Backtest
            backtester = EventDrivenBacktester()
            result = backtester.run(strategy, df)
            
            # 5. Display Results
            self.display_results(result)
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            QMessageBox.critical(self, "Error", f"Backtest failed: {e}")
        finally:
            self.btn_run.setEnabled(True)
            self.btn_run.setText("Run Backtest")

    def display_results(self, result):
        # 1. Metrics
        metrics = [
            ("Total Return", f"{result.total_return:.2f}%"),
            ("Final Capital", f"{result.final_capital:,.0f}"),
            ("MDD", f"{result.mdd:.2f}%"),
            ("Win Rate", f"{result.win_rate:.2f}%"),
            ("Total Trades", str(len(result.trades)))
        ]
        self.metrics_table.setRowCount(len(metrics))
        for i, (k, v) in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(k))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(v))
            
        # 2. Trades
        self.trade_table.setRowCount(len(result.trades))
        for i, t in enumerate(result.trades):
            self.trade_table.setItem(i, 0, QTableWidgetItem(t["time"].strftime("%Y-%m-%d")))
            self.trade_table.setItem(i, 1, QTableWidgetItem(t["type"]))
            self.trade_table.setItem(i, 2, QTableWidgetItem(f"{t['price']:,.0f}"))
            self.trade_table.setItem(i, 3, QTableWidgetItem(str(t["qty"])))
            profit = t.get("profit", 0)
            p_item = QTableWidgetItem(f"{profit:,.0f}" if t["type"] == "SELL" else "-")
            if profit > 0: p_item.setForeground(Qt.GlobalColor.red)
            elif profit < 0: p_item.setForeground(Qt.GlobalColor.blue)
            self.trade_table.setItem(i, 4, p_item)
            
        # 3. Chart
        self.chart_widget.clear()
        if result.equity_curve:
            self.chart_widget.plot(result.equity_curve, pen=pg.mkPen('#00a8ff', width=2))
