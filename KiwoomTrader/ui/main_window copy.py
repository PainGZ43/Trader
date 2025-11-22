import sys
import asyncio
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from trading_manager import TradingManager
from config import Config
from ai.backtester import Backtester
from ai.strategy_optimizer import StrategyOptimizer
from logger import logger

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trader = TradingManager()
        self.backtester = Backtester()
        
        self.setWindowTitle("키움 AI 트레이더 (프리미엄)")
        self.setGeometry(100, 100, 1280, 800)
        
        # Progress bar for backtest
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        self.init_ui()
        self.load_styles()
        
        # Timer for UI updates (1 sec interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)
        
    def load_styles(self):
        try:
            with open("ui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.error(f"Failed to load styles: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Top Bar (Status & Controls)
        top_bar = QHBoxLayout()
        
        self.status_label = QLabel("시스템: 준비")
        self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        
        self.balance_label = QLabel(f"예수금: {self.trader.balance:,.0f} 원")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.start_btn = QPushButton("자동매매 시작")
        self.start_btn.setObjectName("buyBtn") # Reusing style
        self.start_btn.clicked.connect(self.toggle_trading)
        
        self.panic_btn = QPushButton("긴급 정지")
        self.panic_btn.setObjectName("panicBtn")
        self.panic_btn.clicked.connect(self.panic_stop)
        
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("종목명 또는 코드 검색")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self.search_stock)
        
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.search_stock)
        
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.search_btn)
        top_bar.addStretch()
        
        top_bar.addWidget(self.balance_label)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.panic_btn)
        
        main_layout.addLayout(top_bar)
        
        # 2. Content Area (Tabs)
        self.tabs = QTabWidget()
        
        self.tab_dashboard = QWidget()
        self.tab_chart = QWidget()
        self.tab_backtest = QWidget()
        self.tab_settings = QWidget()
        
        self.tabs.addTab(self.tab_dashboard, "대시보드")
        self.tabs.addTab(self.tab_chart, "실시간 차트")
        self.tabs.addTab(self.tab_backtest, "백테스트")
        self.tabs.addTab(self.tab_settings, "설정")
        
        self.init_dashboard()
        self.init_chart()
        self.init_backtest()
        
        main_layout.addWidget(self.tabs)
        
        # 3. Log Console
        log_group = QGroupBox("시스템 로그")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_group.setMaximumHeight(150)
        
        main_layout.addWidget(log_group)
        
        # 4. Progress Bar
        main_layout.addWidget(self.progress_bar)

    def init_dashboard(self):
        layout = QGridLayout()
        
        # Account Summary
        acc_group = QGroupBox("계좌 요약")
        acc_layout = QFormLayout()
        self.lbl_total_asset = QLabel("0")
        self.lbl_daily_profit = QLabel("0 (+0.00%)")
        acc_layout.addRow("총 자산:", self.lbl_total_asset)
        acc_layout.addRow("당일 손익:", self.lbl_daily_profit)
        acc_group.setLayout(acc_layout)
        
        # Active Positions
        pos_group = QGroupBox("보유 종목")
        pos_layout = QVBoxLayout()
        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(5)
        self.pos_table.setHorizontalHeaderLabels(["종목코드", "종목명", "수량", "평단가", "수익률"])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        pos_layout.addWidget(self.pos_table)
        pos_group.setLayout(pos_layout)
        
        layout.addWidget(acc_group, 0, 0)
        layout.addWidget(pos_group, 1, 0)
        self.tab_dashboard.setLayout(layout)

    def init_chart(self):
        layout = QVBoxLayout()
        
        # Chart Widget
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('#1e1e1e')
        self.chart_widget.showGrid(x=True, y=True)
        layout.addWidget(self.chart_widget)
        
        self.tab_chart.setLayout(layout)

    def init_backtest(self):
        layout = QVBoxLayout()
        
        control_layout = QHBoxLayout()
        self.bt_code_input = QLineEdit("005930")
        self.bt_start_btn = QPushButton("백테스트 실행")
        self.bt_start_btn.clicked.connect(self.run_backtest)
        self.bt_optimize_btn = QPushButton("🚀 전략 최적화")
        self.bt_optimize_btn.clicked.connect(self.run_optimization)
        self.bt_optimize_btn.setStyleSheet("background-color: #6c5ce7; color: white; font-weight: bold;")
        control_layout.addWidget(QLabel("종목코드:"))
        control_layout.addWidget(self.bt_code_input)
        control_layout.addWidget(self.bt_start_btn)
        control_layout.addWidget(self.bt_optimize_btn)
        control_layout.addStretch()
        
        self.bt_result_text = QTextEdit()
        self.bt_result_text.setReadOnly(True)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.bt_result_text)
        self.tab_backtest.setLayout(layout)

    def update_ui(self):
        # Update Status
        if self.trader.is_running:
            self.status_label.setText("시스템: 실행 중")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        else:
            self.status_label.setText("시스템: 중지됨")
            self.status_label.setStyleSheet("color: #d63031; font-weight: bold;")
            
        # Update Balance
        self.balance_label.setText(f"예수금: {self.trader.balance:,.0f} 원")
        self.lbl_total_asset.setText(f"{self.trader.total_assets:,.0f} 원")
        
        # Update Positions Table
        self.pos_table.setRowCount(len(self.trader.portfolio))
        for i, (code, data) in enumerate(self.trader.portfolio.items()):
            self.pos_table.setItem(i, 0, QTableWidgetItem(code))
            self.pos_table.setItem(i, 1, QTableWidgetItem(data.get('name', 'Unknown')))
            self.pos_table.setItem(i, 2, QTableWidgetItem(str(data['qty'])))
            self.pos_table.setItem(i, 3, QTableWidgetItem(f"{data['avg_price']:,.0f}"))
            
            # Mock current price for profit calc
            curr_price = data['avg_price'] # Placeholder
            profit_pct = 0.0
            
            item_profit = QTableWidgetItem(f"{profit_pct:.2f}%")
            if profit_pct > 0:
                item_profit.setForeground(QColor("#00b894"))
            elif profit_pct < 0:
                item_profit.setForeground(QColor("#d63031"))
            self.pos_table.setItem(i, 4, item_profit)

    def toggle_trading(self):
        if not self.trader.is_running:
            asyncio.create_task(self.trader.start())
            self.start_btn.setText("자동매매 중지")
            self.start_btn.setStyleSheet("background-color: #d63031;")
            self.log("자동매매 시작됨")
        else:
            asyncio.create_task(self.trader.stop())
            self.start_btn.setText("자동매매 시작")
            self.start_btn.setStyleSheet("background-color: #00b894;")
            self.log("자동매매 중지됨")

    def panic_stop(self):
        asyncio.create_task(self.trader.stop())
        self.log("긴급 정지 발동!")
        QMessageBox.critical(self, "긴급 정지", "긴급 정지가 발동되었습니다! 모든 작업이 중단됩니다.")

    def run_backtest(self):
        code = self.bt_code_input.text()
        
        # Calculate dates: Last 1 year
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        
        self.log(f"{code} 백테스트 실행 중... ({start_date} ~ {end_date})")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Define progress callback
        def progress_callback(pct):
            self.progress_bar.setValue(pct)
            QApplication.processEvents()  # Update UI
        
        # Run backtest with progress callback
        result = self.backtester.run(code, start_date, end_date, progress_callback=progress_callback)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Process Daily Summary with BUY/SELL separation
        daily_stats = {}
        for trade in result['trades']:
            date = trade['date'][:10]  # Extract date part only (YYYY-MM-DD)
            if date not in daily_stats:
                daily_stats[date] = {'buy': 0, 'sell': 0, 'profit': 0}
            
            if trade['type'] == 'BUY':
                daily_stats[date]['buy'] += 1
            elif trade['type'] == 'SELL':
                daily_stats[date]['sell'] += 1
                daily_stats[date]['profit'] += trade.get('profit', 0)

        # Build HTML daily report with colors
        daily_report_html = "<h3>📊 일별 매매 요약</h3><table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>"
        daily_report_html += "<tr style='background-color: #2d3436; color: white;'><th>날짜</th><th>매수</th><th>매도</th><th>손익</th></tr>"
        
        for date, stats in sorted(daily_stats.items()):
            profit = stats['profit']
            if profit > 0:
                profit_color = '#00b894'
                profit_str = f"+{profit:,.0f}원"
            elif profit < 0:
                profit_color = '#d63031'
                profit_str = f"{profit:,.0f}원"
            else:
                profit_color = '#636e72'
                profit_str = "0원"
            
            daily_report_html += f"<tr>"
            daily_report_html += f"<td>{date}</td>"
            daily_report_html += f"<td style='color: #0984e3;'>{stats['buy']}회</td>"
            daily_report_html += f"<td style='color: #e17055;'>{stats['sell']}회</td>"
            daily_report_html += f"<td style='color: {profit_color}; font-weight: bold;'>{profit_str}</td>"
            daily_report_html += "</tr>"
        
        daily_report_html += "</table>"
        
        # Build main report in HTML format
        total_profit_color = '#00b894' if result['profit_pct'] > 0 else '#d63031'
        
        report_html = f"""
        <html>
        <body style='font-family: "Malgun Gothic", sans-serif; background-color: #1e1e1e; color: #dfe6e9;'>
            <h2 style='color: #74b9ff;'>📈 백테스트 결과</h2>
            <table style='width: 100%;'>
                <tr><td><b>기간:</b></td><td>{start_date} ~ {end_date}</td></tr>
                <tr><td><b>종목코드:</b></td><td>{code}</td></tr>
                <tr><td><b>최종 잔고:</b></td><td>{result['final_balance']:,.0f}원</td></tr>
                <tr><td><b>총 수익:</b></td><td style='color: {total_profit_color}; font-weight: bold;'>{result['total_profit']:,.0f}원 ({result['profit_pct']:.2f}%)</td></tr>
                <tr><td><b>매매 횟수:</b></td><td>{result['trade_count']}회</td></tr>
                <tr><td><b>MDD:</b></td><td style='color: #d63031;'>{result['mdd']:.2f}%</td></tr>
            </table>
            <br>
            {daily_report_html}
        </body>
        </html>
        """
        
        self.bt_result_text.setHtml(report_html)
        self.log("백테스트 완료")
    
    def run_optimization(self):
        """전략 파라미터 최적화 실행"""
        code = self.bt_code_input.text()
        
       # Calculate dates: Last 1 year
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        
        self.log(f"🚀 전략 최적화 시작... (종목: {code}, 기간: {start_date} ~ {end_date})")
        self.log("⚠️ 최적화는 수십 ~ 수백 번의 백테스트를 실행하므로 시간이 걸릴 수 있습니다.")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Define progress callback
        def progress_callback(pct):
            self.progress_bar.setValue(pct)
            QApplication.processEvents()
        
        # Run optimization
        optimizer = StrategyOptimizer()
        best_result, best_params, all_results = optimizer.optimize(
            code, start_date, end_date, progress_callback=progress_callback
        )
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Get top 5 results
        top_results = optimizer.get_top_results(5)
        
        # Build HTML report
        report_html = f"""
        <html>
        <body style='font-family: "Malgun Gothic", sans-serif; background-color: #1e1e1e; color: #dfe6e9;'>
            <h2 style='color: #6c5ce7;'>🚀 전략 최적화 결과</h2>
            <h3 style='color: #74b9ff;'>📊 최고 성과 전략</h3>
            <table style='width: 100%; border: 1px solid #636e72;' cellpadding='5'>
                <tr style='background-color: #2d3436; color: white;'>
                    <th>파라미터</th><th>값</th>
                </tr>
                <tr><td>볼륨 임계값</td><td>{best_params['vol_threshold']}</td></tr>
                <tr><td>AI 점수 임계값</td><td>{best_params['ai_threshold']}</td></tr>
                <tr><td>익절 목표</td><td>{best_params['take_profit']}%</td></tr>
                <tr><td>손절 목표</td><td>{best_params['stop_loss']}%</td></tr>
                <tr><td>쿨다운</td><td>{best_params['cooldown']}분</td></tr>
            </table>
            <br>
            <h4 style='color: #00b894;'>✨ 성과</h4>
            <table style='width: 100%;'>
                <tr><td><b>총 수익:</b></td><td style='color: #00b894; font-weight: bold;'>{best_result['total_profit']:,.0f}원 ({best_result['profit_pct']:.2f}%)</td></tr>
                <tr><td><b>최종 잔고:</b></td><td>{best_result['final_balance']:,.0f}원</td></tr>
                <tr><td><b>매매 횟수:</b></td><td>{best_result['trade_count']}회</td></tr>
                <tr><td><b>MDD:</b></td><td style='color: #d63031;'>{best_result['mdd']:.2f}%</td></tr>
                <tr><td><b>평가 점수:</b></td><td style='color: #fdcb6e; font-weight: bold;'>{best_result['score']:.2f}</td></tr>
            </table>
            <br>
            <h4>🏆 상위 5개 전략</h4>
            <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
                <tr style='background-color: #2d3436; color: white;'>
                    <th>순위</th><th>수익률</th><th>MDD</th><th>매매</th><th>점수</th><th>TP/SL</th><th>AI</th>
                </tr>
        """
        
        for idx, res in enumerate(top_results, 1):
            profit_color = '#00b894' if res['profit_pct'] > 0 else '#d63031'
            report_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td style='color: {profit_color}; font-weight: bold;'>{res['profit_pct']:.2f}%</td>
                    <td style='color: #d63031;'>{res['mdd']:.2f}%</td>
                    <td>{res['trade_count']}회</td>
                    <td style='color: #fdcb6e;'>{res['score']:.2f}</td>
                    <td>{res['params']['take_profit']}/{res['params']['stop_loss']}</td>
                    <td>{res['params']['ai_threshold']}</td>
                </tr>
            """
        
        report_html += """
            </table>
            <br>
            <p style='color: #636e72; font-size: 12px;'>
                ⓘ 평가 점수 = 수익률 - (MDD / 2)<br>
                높은 수익률과 낮은 MDD를 동시에 고려합니다.
            </p>
        </body>
        </html>
        """
        
        self.bt_result_text.setHtml(report_html)
        self.log(f"✅ 최적화 완료! 총 {len(all_results)}개 조합 테스트 완료")


    def log(self, message):
        self.log_text.append(f"[{QTime.currentTime().toString()}] {message}")

    def search_stock(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
            
        asyncio.create_task(self._perform_search(keyword))
        
    async def _perform_search(self, keyword):
        # Fetch master list
        stocks = await self.trader.api.get_master_list()
        
        # Filter
        results = [s for s in stocks if keyword in s['name'] or keyword in s['code']]
        
        if not results:
            QMessageBox.information(self, "검색 결과", "검색된 종목이 없습니다.")
            return
            
        if len(results) == 1:
            # Exact match or only one result
            self.select_stock(results[0])
        else:
            # Multiple results - Show dialog
            self.show_search_dialog(results)
            
    def show_search_dialog(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle("종목 선택")
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for s in results:
            list_widget.addItem(f"{s['name']} ({s['code']})")
            
        def on_select():
            idx = list_widget.currentRow()
            if idx >= 0:
                self.select_stock(results[idx])
                dialog.accept()
                
        list_widget.itemDoubleClicked.connect(on_select)
        
        select_btn = QPushButton("선택")
        select_btn.clicked.connect(on_select)
        
        layout.addWidget(list_widget)
        layout.addWidget(select_btn)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def select_stock(self, stock):
        self.log(f"종목 선택: {stock['name']} ({stock['code']})")
        self.search_input.setText("")
        self.bt_code_input.setText(stock['code']) # Update backtest input
        # Future: Update chart with this stock
        QMessageBox.information(self, "종목 선택", f"선택된 종목: {stock['name']}\n백테스트 및 차트 대상이 변경되었습니다.")
