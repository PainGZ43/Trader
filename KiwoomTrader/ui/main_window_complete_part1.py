# Premium Kiwoom AI Trader - Complete Main Window
# Part 1: Imports and Class Definition

import sys
import asyncio
import threading
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import numpy as np

from trading_manager import TradingManager
from config import Config
from ai.backtester import Backtester
from ai.strategy_optimizer import StrategyOptimizer
from ai.recommender import StockRecommender
from watchlist_manager import WatchlistManager
from strategy_manager import StrategyManager
from settings_manager import settings
from logger import logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trader = TradingManager()
        self.backtester = Backtester()
        self.watchlist_manager = WatchlistManager()
        self.recommender = StockRecommender()
        self.strategy_manager = StrategyManager()
        
        self.setWindowTitle("키움 AI 트레이더 (프리미엄)")
        self.setGeometry(100, 100, 1400, 900)
        
        # Training cancel flag
        self.training_cancel_flag = False
        
        # Progress bar for backtest
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        self.init_ui()
        self.load_styles()
        
        # Load watchlist on startup
        self.load_watchlist()
        
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
        
        # Initialize Log Console early (so self.log works)
        log_group = QGroupBox("시스템 로그")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 1. Top Bar (Status & Controls)
        top_bar = QHBoxLayout()
        
        self.status_label = QLabel("시스템: 준비")
        self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        
        self.balance_label = QLabel(f"예수금: {self.trader.balance:,.0f} 원")
        self.balance_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # New Account Info Labels
        self.total_asset_label = QLabel("총 자산: 0 원")
        self.total_asset_label.setStyleSheet("font-size: 14px; color: #dfe6e9; margin-left: 15px;")
        
        self.daily_profit_label = QLabel("당일 손익: 0 (+0.00%)")
        self.daily_profit_label.setStyleSheet("font-size: 14px; color: #dfe6e9; margin-left: 10px;")
        
        self.start_btn = QPushButton("자동매매 시작")
        self.start_btn.setObjectName("buyBtn")
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
        top_bar.addWidget(self.total_asset_label)
        top_bar.addWidget(self.daily_profit_label)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.panic_btn)
        
        main_layout.addLayout(top_bar)
        
        # 2. Content Area (Tabs)
        self.tabs = QTabWidget()
        
        self.tab_dashboard = QWidget()
        self.tab_chart = QWidget()
        self.tab_watchlist = QWidget()
        self.tab_recommend = QWidget()
        self.tab_backtest = QWidget()
        self.tab_settings = QWidget()
        
        self.tabs.addTab(self.tab_dashboard, "대시보드")
        self.tab_chart = QWidget()
        self.tabs.addTab(self.tab_watchlist, "⭐ 관심종목")
        self.tabs.addTab(self.tab_recommend, "🎯 AI 추천")
        self.tabs.addTab(self.tab_backtest, "백테스트")
        self.tabs.addTab(self.tab_settings, "설정")
        
        self.init_dashboard()
        self.init_chart()
        self.init_watchlist()
        self.init_recommend()
        self.init_backtest()
        self.init_settings()
        
        main_layout.addWidget(self.tabs)
        
        # 3. Add Log Console to Layout
        main_layout.addWidget(log_group)
        
        # 4. Progress Bar
        main_layout.addWidget(self.progress_bar)
