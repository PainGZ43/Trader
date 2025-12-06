import asyncio
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QFormLayout, QSplitter, QWidget, QMessageBox, QTabWidget, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate, QUrl, QThread, pyqtSignal
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
    WEBENGINE_ERROR = None
except ImportError as e:
    print(f"DEBUG: Failed to import QWebEngineView: {e}")
    HAS_WEBENGINE = False
    WEBENGINE_ERROR = str(e)
    from PyQt6.QtWidgets import QTextBrowser as QWebEngineView # Fallback
except Exception as e:
    print(f"DEBUG: Unexpected error importing QWebEngineView: {e}")
    HAS_WEBENGINE = False
    WEBENGINE_ERROR = str(e)
    from PyQt6.QtWidgets import QTextBrowser as QWebEngineView # Fallback
import pyqtgraph as pg
from qasync import asyncSlot

from strategy.backtester import EventDrivenBacktester
from strategy.strategies import VolatilityBreakoutStrategy, MovingAverageCrossoverStrategy, RSIStrategy, BollingerBandStrategy
from data.data_collector import data_collector
from core.logger import get_logger

class BacktestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("백테스트 연구소")
        self.resize(1400, 900)
        self.logger = get_logger("BacktestUI")
        
        self.init_ui()
        
        # Auto-update data
        self.start_data_update()

    def start_data_update(self):
        self.update_thread = DataUpdateThread()
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.start()
        
        # Show status in title or status bar
        self.setWindowTitle("백테스트 연구소 (데이터 업데이트 중...)")

    def on_update_finished(self, success, msg):
        if success:
            self.setWindowTitle("백테스트 연구소 (데이터 최신)")
            self.logger.info(f"Data update finished: {msg}")
        else:
            self.setWindowTitle("백테스트 연구소 (업데이트 실패)")
            self.logger.error(f"Data update failed: {msg}")
        
    def init_ui(self):
        layout = QVBoxLayout(self)


        
        # Tabs for Modes
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Single Stock (Interactive)
        self.tab_single = QWidget()
        self.init_single_ui(self.tab_single)
        self.tabs.addTab(self.tab_single, "단일 종목 (API)")
        
        # Tab 2: Bulk Backtest
        self.tab_bulk = QWidget()
        self.init_bulk_ui(self.tab_bulk)
        self.tabs.addTab(self.tab_bulk, "일괄 백테스트 (Batch)")

        # Tab 3: Optimization
        self.tab_opt = QWidget()
        self.init_optimization_ui(self.tab_opt)
        self.tabs.addTab(self.tab_opt, "최적화 (Optimization)")

    def init_single_ui(self, parent):
        layout = QVBoxLayout(parent)
        
        # Top Control Panel
        control_group = QGroupBox("설정")
        control_layout = QHBoxLayout()
        
        # Strategy Selection
        self.combo_strategy = QComboBox()
        # Use Registry
        from strategy.registry import StrategyRegistry
        StrategyRegistry.initialize()
        self.combo_strategy.addItems(StrategyRegistry.get_all_strategies())
        
        control_layout.addWidget(QLabel("전략:"))
        control_layout.addWidget(self.combo_strategy)
        
        # Symbol
        from ui.widgets.symbol_search import SymbolSearchWidget
        self.txt_symbol = SymbolSearchWidget()
        control_layout.addWidget(QLabel("종목:"))
        control_layout.addWidget(self.txt_symbol)
        
        # Date Range
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setCalendarPopup(True)
        control_layout.addWidget(QLabel("시작일:"))
        control_layout.addWidget(self.date_start)
        
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setCalendarPopup(True)
        control_layout.addWidget(QLabel("종료일:"))
        control_layout.addWidget(self.date_end)
        
        # Run Button
        self.btn_run = QPushButton("백테스트 실행")
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
        self.chart_widget.setTitle("자산 곡선 (Equity Curve)", color="w", size="12pt")
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        self.chart_widget.setLabel('left', '자산 (KRW)')
        self.chart_widget.setLabel('bottom', '시간')
        splitter.addWidget(self.chart_widget)
        
        # 2. Results Area (Metrics + Trade List)
        results_widget = QWidget()
        results_layout = QHBoxLayout(results_widget)
        
        # Metrics Table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["지표", "값"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)
        results_layout.addWidget(self.metrics_table, 1)
        
        # Trade List Table
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(5)
        self.trade_table.setHorizontalHeaderLabels(["시간", "유형", "가격", "수량", "수익"])
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trade_table.verticalHeader().setVisible(False)
        results_layout.addWidget(self.trade_table, 2)
        
        splitter.addWidget(results_widget)
        layout.addWidget(splitter)

    def init_bulk_ui(self, parent):
        layout = QVBoxLayout(parent)
        
        # Controls
        control_layout = QHBoxLayout()
        
        self.combo_bulk_strategy = QComboBox()
        from strategy.registry import StrategyRegistry
        self.combo_bulk_strategy.addItems(StrategyRegistry.get_all_strategies())
        control_layout.addWidget(QLabel("전략:"))
        control_layout.addWidget(self.combo_bulk_strategy)
        
        control_layout.addWidget(QLabel("종목 제한:"))
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(0, 5000)
        self.spin_limit.setValue(100)
        self.spin_limit.setSpecialValueText("전체")
        control_layout.addWidget(self.spin_limit)
        
        self.btn_bulk_run = QPushButton("대량 백테스트 실행")
        self.btn_bulk_run.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_bulk_run.clicked.connect(self.run_bulk_backtest)
        control_layout.addWidget(self.btn_bulk_run)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Web View for Report
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Load existing report if available
        report_path = os.path.abspath("data/backtest_report.html")
        if os.path.exists(report_path):
            if HAS_WEBENGINE:
                self.web_view.setUrl(QUrl.fromLocalFile(report_path))
            else:
                error_msg = f"<br>Error: {WEBENGINE_ERROR}" if WEBENGINE_ERROR else ""
                self.web_view.setHtml(f"<h1>보고서를 보려면 PyQt6-WebEngine을 설치하세요.</h1><p>파일 위치: {report_path}</p><p style='color:red'>{error_msg}</p>")

    def init_optimization_ui(self, parent):
        layout = QHBoxLayout(parent)
        
        # Left: Configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Strategy Selection
        self.opt_strategy_combo = QComboBox()
        from strategy.registry import StrategyRegistry
        self.opt_strategy_combo.addItems(StrategyRegistry.get_all_strategies())
        self.opt_strategy_combo.currentTextChanged.connect(self.load_opt_params)
        left_layout.addWidget(QLabel("전략:"))
        left_layout.addWidget(self.opt_strategy_combo)
        
        # Symbol
        from ui.widgets.symbol_search import SymbolSearchWidget
        self.opt_symbol = SymbolSearchWidget()
        left_layout.addWidget(QLabel("종목:"))
        left_layout.addWidget(self.opt_symbol)
        
        # Date Range
        self.opt_date_start = QDateEdit()
        self.opt_date_start.setDate(QDate.currentDate().addMonths(-6))
        self.opt_date_start.setCalendarPopup(True)
        left_layout.addWidget(QLabel("시작일:"))
        left_layout.addWidget(self.opt_date_start)
        
        self.opt_date_end = QDateEdit()
        self.opt_date_end.setDate(QDate.currentDate())
        self.opt_date_end.setCalendarPopup(True)
        left_layout.addWidget(QLabel("종료일:"))
        left_layout.addWidget(self.opt_date_end)
        
        # Parameter Ranges
        self.opt_param_group = QGroupBox("파라미터 범위 설정")
        self.opt_param_layout = QFormLayout()
        self.opt_param_group.setLayout(self.opt_param_layout)
        left_layout.addWidget(self.opt_param_group)
        
        # Run Button
        self.btn_opt_run = QPushButton("최적화 실행")
        self.btn_opt_run.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 10px;")
        self.btn_opt_run.clicked.connect(self.run_optimization)
        left_layout.addWidget(self.btn_opt_run)
        
        left_layout.addStretch()
        layout.addWidget(left_panel, 1)
        
        # Right: Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.opt_results_table = QTableWidget()
        self.opt_results_table.setColumnCount(4) # Params, Return, MDD, Trades
        self.opt_results_table.setHorizontalHeaderLabels(["파라미터", "수익률", "MDD", "거래수"])
        self.opt_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.opt_results_table)
        
        layout.addWidget(right_panel, 2)
        
        # Initial Load
        self.load_opt_params(self.opt_strategy_combo.currentText())
        self.opt_param_inputs = {}

    def load_opt_params(self, strategy_name):
        # Clear existing
        while self.opt_param_layout.count():
            child = self.opt_param_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.opt_param_inputs = {}
        
        from strategy.registry import StrategyRegistry
        schema = StrategyRegistry.get_strategy_schema(strategy_name)
        
        for key, meta in schema.items():
            if meta["type"] in ["int", "float"]:
                # Range Input: Start, End, Step
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0,0,0,0)
                
                start_spin = QSpinBox() if meta["type"] == "int" else QDoubleSpinBox()
                end_spin = QSpinBox() if meta["type"] == "int" else QDoubleSpinBox()
                step_spin = QSpinBox() if meta["type"] == "int" else QDoubleSpinBox()
                
                # Configure Ranges
                min_val = meta.get("min", 0)
                max_val = meta.get("max", 1000)
                default_val = meta.get("default", 0)
                
                if meta["type"] == "float":
                    # QDoubleSpinBox is already imported at top level
                    start_spin = QDoubleSpinBox()
                    end_spin = QDoubleSpinBox()
                    step_spin = QDoubleSpinBox()
                    for s in [start_spin, end_spin, step_spin]:
                        s.setRange(min_val, max_val)
                        s.setSingleStep(0.1)
                        s.setDecimals(2)
                    step_spin.setValue(0.1)
                else:
                    for s in [start_spin, end_spin, step_spin]:
                        s.setRange(int(min_val), int(max_val))
                    step_spin.setValue(1)
                
                # Defaults: Start=Default, End=Default+Step*2
                start_spin.setValue(default_val)
                end_spin.setValue(default_val)
                
                row_layout.addWidget(QLabel("시작:"))
                row_layout.addWidget(start_spin)
                row_layout.addWidget(QLabel("종료:"))
                row_layout.addWidget(end_spin)
                row_layout.addWidget(QLabel("간격:"))
                row_layout.addWidget(step_spin)
                
                self.opt_param_layout.addRow(meta.get("desc", key), row_widget)
                self.opt_param_inputs[key] = (start_spin, end_spin, step_spin, meta["type"])

    @asyncSlot()
    async def run_optimization(self):
        self.btn_opt_run.setEnabled(False)
        self.btn_opt_run.setText("최적화 중...")
        
        try:
            strategy_name = self.opt_strategy_combo.currentText()
            symbol = self.opt_symbol.get_current_code()
            if not symbol:
                self._show_message("오류", "유효한 종목을 선택해주세요.", QMessageBox.Icon.Warning)
                return
                
            start_date = self.opt_date_start.date().toString("yyyyMMdd")
            end_date = self.opt_date_end.date().toString("yyyyMMdd")
            
            # 1. Prepare Data (From CSV)
            df = self.load_data_from_csv(symbol, start_date, end_date)
            
            if df is None:
                 self._show_message("오류", "데이터 파일을 찾을 수 없습니다.\nscripts/manage_data.py를 실행하세요.", QMessageBox.Icon.Warning)
                 return
                 
            if df.empty:
                self._show_message("오류", "데이터가 없습니다.", QMessageBox.Icon.Warning)
                return
            
            if df.empty:
                self._show_message("오류", "데이터가 없습니다.", QMessageBox.Icon.Warning)
                return
                
            # 2. Prepare Param Ranges
            import numpy as np
            param_ranges = {}
            for key, (start, end, step, type_) in self.opt_param_inputs.items():
                s = start.value()
                e = end.value()
                st = step.value()
                
                if s > e:
                    self._show_message("오류", f"{key}의 범위가 잘못되었습니다.", QMessageBox.Icon.Warning)
                    return
                    
                if type_ == "int":
                    # range is exclusive at end, so +1 if we want to include end
                    # But numpy arange is better for floats, range for ints
                    # Let's use a list
                    vals = []
                    curr = s
                    while curr <= e:
                        vals.append(int(curr))
                        curr += st
                        if st == 0: break
                    param_ranges[key] = vals
                else:
                    # Float
                    # Use numpy arange but be careful with float precision
                    # Or just simple loop
                    vals = []
                    curr = s
                    while curr <= e + 0.00001: # Epsilon for float comparison
                        vals.append(float(curr))
                        curr += st
                        if st == 0: break
                    param_ranges[key] = vals
            
            # 3. Run Optimization
            from optimization.optimizer import Optimizer
            from strategy.registry import StrategyRegistry
            
            strategy_cls = StrategyRegistry.get_strategy_class(strategy_name)
            optimizer = Optimizer()
            
            # Run in thread/process to avoid blocking UI
            # Since Optimizer uses ProcessPoolExecutor, we can call it directly?
            # No, the main thread will block waiting for results.
            # We should wrap it in run_in_executor
            
            loop = asyncio.get_event_loop()
            results_df = await loop.run_in_executor(
                None, 
                optimizer.run_optimization, 
                strategy_cls, 
                df, 
                param_ranges
            )
            
            # 4. Display Results
            self.display_opt_results(results_df)
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            self._show_message("오류", f"최적화 실패: {e}", QMessageBox.Icon.Critical)
        finally:
            self.btn_opt_run.setEnabled(True)
            self.btn_opt_run.setText("최적화 실행")

    def display_opt_results(self, df):
        self.opt_results_table.setRowCount(0)
        if df.empty:
            return
            
        self.opt_results_table.setRowCount(len(df))
        
        # Columns: Params, Return, MDD, Trades
        # Params are scattered in columns, need to combine
        # Metrics: total_return, mdd, trades (count)
        
        # Identify param columns
        # All columns that are not metrics
        metric_cols = ['total_return', 'final_capital', 'mdd', 'win_rate', 'trades']
        param_cols = [c for c in df.columns if c not in metric_cols]
        
        for i, row in df.iterrows():
            # 1. Params String
            params_str = ", ".join([f"{k}={row[k]}" for k in param_cols])
            self.opt_results_table.setItem(i, 0, QTableWidgetItem(params_str))
            
            # 2. Return
            ret = row.get('total_return', 0)
            item_ret = QTableWidgetItem(f"{ret:.2f}%")
            if ret > 0: item_ret.setForeground(Qt.GlobalColor.red)
            elif ret < 0: item_ret.setForeground(Qt.GlobalColor.blue)
            self.opt_results_table.setItem(i, 1, item_ret)
            
            # 3. MDD
            mdd = row.get('mdd', 0)
            self.opt_results_table.setItem(i, 2, QTableWidgetItem(f"{mdd:.2f}%"))
            
            # 4. Trades
            trades = row.get('trades', []) # This might be a list if returned from backtester
            # If we returned full trade list in metrics, it's heavy.
            # Optimizer _run_single_backtest returns metrics. 
            # Backtester.run returns BacktestResult object.
            # We need to check what Backtester returns.
            # In Optimizer, we returned result['metrics'].
            # Backtester.run returns a dict? No, it returns BacktestResult object.
            # Let's check Backtester.run return type.
            
            # Assuming Optimizer returns dict with 'total_return', 'mdd', etc.
            # If 'trades' is count, use it. If list, len().
            # In Optimizer we did: result = backtester.run(df); return result['metrics']
            # We need to ensure Backtester.run returns something with 'metrics' key or attribute.
            # Actually Backtester returns BacktestResult object.
            # I need to fix Optimizer to extract metrics from BacktestResult object.
            
            # For now assuming 'trades' is in the row and it is a list or count
            t_val = row.get('trades', 0)
            if isinstance(t_val, list): t_val = len(t_val)
            self.opt_results_table.setItem(i, 3, QTableWidgetItem(str(t_val)))

    @asyncSlot()
    async def run_backtest(self):
        self.btn_run.setEnabled(False)
        self.btn_run.setText("실행 중...")
        
        try:
            # 1. Get Parameters
            strategy_name = self.combo_strategy.currentText()
            symbol = self.txt_symbol.get_current_code()
            if not symbol:
                self._show_message("오류", "유효한 종목을 선택해주세요.", QMessageBox.Icon.Warning)
                return
            start_date = self.date_start.date().toString("yyyyMMdd")
            end_date = self.date_end.date().toString("yyyyMMdd")
            
            # 2. Fetch Data (From CSV)
            df = self.load_data_from_csv(symbol, start_date, end_date)
            
            if df is None:
                 self._show_message("오류", "데이터 파일을 찾을 수 없습니다.\nscripts/manage_data.py를 실행하세요.", QMessageBox.Icon.Warning)
                 return
                 
            if df.empty:
                self._show_message("오류", "선택한 기간에 데이터가 없습니다.", QMessageBox.Icon.Warning)
                return
            
            if df.empty:
                self._show_message("오류", "선택한 기간에 데이터가 없습니다.", QMessageBox.Icon.Warning)
                return

            # 3. Initialize Strategy
            from strategy.registry import StrategyRegistry
            strategy_cls = StrategyRegistry.get_strategy_class(strategy_name)
            if not strategy_cls:
                return
            
            # Use default params from schema for now, or load from config
            # For single backtest, we might want to allow editing params too.
            # But for now, let's just use defaults or what's in config.
            strategy = strategy_cls("BT_SINGLE", symbol)
            
            # Load params from config
            from core.config import config
            schema = strategy_cls.get_parameter_schema()
            params = {}
            for key, meta in schema.items():
                params[key] = config.get(f"strategy.{strategy_name}.{key}", meta.get("default"))
                
            strategy.initialize(params) 
            
            # 4. Run Backtest
            backtester = EventDrivenBacktester()
            result = backtester.run(strategy, df)
            
            # 5. Display Results
            self.display_results(result)
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            self._show_message("오류", f"백테스트 실패: {e}", QMessageBox.Icon.Critical)
        finally:
            self.btn_run.setEnabled(True)
            self.btn_run.setText("백테스트 실행")

    def run_bulk_backtest(self):
        self.btn_bulk_run.setEnabled(False)
        self.btn_bulk_run.setText("대량 백테스트 실행 중...")
        
        # Run script in background?
        # For simplicity, we run it using subprocess or direct import in a thread.
        # Direct import is better but might block UI if not threaded.
        # Let's use QThread or asyncio loop run_in_executor.
        
        import subprocess
        
        strategy = self.combo_bulk_strategy.currentText()
        limit = self.spin_limit.value()
        
        cmd = [sys.executable, "scripts/run_backtest_with_csv.py", "--strategy", strategy, "--limit", str(limit)]
        
        # We should run this in a thread to avoid freezing UI
        # We should run this in a thread to avoid freezing UI
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class BacktestThread(QThread):
            finished = pyqtSignal(bool, str)
            
            def run(self):
                try:
                    # Run command
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                    if result.returncode == 0:
                        self.finished.emit(True, result.stdout)
                    else:
                        self.finished.emit(False, result.stderr)
                except Exception as e:
                    self.finished.emit(False, str(e))
                    
        self.bt_thread = BacktestThread()
        self.bt_thread.finished.connect(self.on_bulk_finished)
        self.bt_thread.start()
        
    def on_bulk_finished(self, success, output):
        self.btn_bulk_run.setEnabled(True)
        self.btn_bulk_run.setText("대량 백테스트 실행")
        
        if success:
            # Reload Web View
            report_path = os.path.abspath("data/backtest_report.html")
            if os.path.exists(report_path):
                if HAS_WEBENGINE:
                    self.web_view.setUrl(QUrl.fromLocalFile(report_path))
                else:
                    error_msg = f"<br>Error: {WEBENGINE_ERROR}" if WEBENGINE_ERROR else ""
                    self.web_view.setHtml(f"<h1>보고서를 보려면 PyQt6-WebEngine을 설치하세요.</h1><p>파일 위치: {report_path}</p><p style='color:red'>{error_msg}</p>")
                QMessageBox.information(self, "성공", "백테스트 완료!\n보고서가 업데이트되었습니다.")
            else:
                QMessageBox.warning(self, "경고", "백테스트가 완료되었으나 보고서 파일을 찾을 수 없습니다.")
        else:
            QMessageBox.critical(self, "오류", f"백테스트 실패:\n{output}")

    def display_results(self, result):
        # 1. Metrics
        metrics = [
            ("총 수익률", f"{result.total_return:.2f}%"),
            ("최종 자산", f"{result.final_capital:,.0f}"),
            ("최대 낙폭 (MDD)", f"{result.mdd:.2f}%"),
            ("승률", f"{result.win_rate:.2f}%"),
            ("총 거래 횟수", str(len(result.trades)))
        ]
        self.metrics_table.setRowCount(len(metrics))

    def load_data_from_csv(self, symbol, start_date, end_date):
        """
        Load data from local CSV file.
        """
        csv_path = os.path.join("data", "historical_data_2020.csv")
        if not os.path.exists(csv_path):
            return None
            
        try:
            # Check if we have cached data
            if not hasattr(self, "_cached_csv_data") or self._cached_csv_data is None:
                self.logger.info(f"Loading CSV data from {csv_path}...")
                self._cached_csv_data = pd.read_csv(csv_path, dtype={'Code': str}) # Ensure Code is string
                self._cached_csv_data['Date'] = pd.to_datetime(self._cached_csv_data['Date'])
            
            df = self._cached_csv_data
            
            # Filter by Symbol
            df_sym = df[df['Code'] == symbol].copy()
            if df_sym.empty:
                return pd.DataFrame()
                
            # Filter by Date
            # start_date, end_date are strings "YYYYMMDD"
            s_date = datetime.strptime(start_date, "%Y%m%d")
            e_date = datetime.strptime(end_date, "%Y%m%d")
            
            mask = (df_sym['Date'] >= s_date) & (df_sym['Date'] <= e_date)
            df_sym = df_sym.loc[mask]
            
            # Rename columns to match what Backtester expects (lowercase)
            # CSV: Date, Code, Name, Open, High, Low, Close, Volume
            # Expected: timestamp, open, high, low, close, volume
            df_sym = df_sym.rename(columns={
                "Date": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            df_sym.set_index('timestamp', inplace=True)
            df_sym.sort_index(inplace=True)
            
            return df_sym
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return None
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

    def _show_message(self, title, msg, icon=QMessageBox.Icon.Information):
        """
        Show message box asynchronously to avoid blocking async loop.
        """
        from PyQt6.QtCore import QTimer
        def show():
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setText(msg)
            box.setIcon(icon)
            box.exec()
        QTimer.singleShot(0, show)

class DataUpdateThread(QThread):
    finished = pyqtSignal(bool, str)
    
    def run(self):
        try:
            import subprocess
            # Run manage_data.py --mode update
            # We don't need --days here, let it update everything needed (incremental)
            cmd = [sys.executable, "scripts/manage_data.py", "--mode", "update"]
            
            # Use startupinfo to hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                startupinfo=startupinfo
            )
            
            if result.returncode == 0:
                self.finished.emit(True, result.stdout)
            else:
                self.finished.emit(False, result.stderr)
                
        except Exception as e:
            self.finished.emit(False, str(e))
