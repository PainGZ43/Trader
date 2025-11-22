"""
차트 위젯 - 업비트 스타일
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,  
                             QLabel, QSplitter, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf
import pandas as pd
from api.upbit_api import UpbitAPI


class ChartWidget(QWidget):
    """차트 위젯 - 업비트 스타일"""
    
    def __init__(self):
        super().__init__()
        self.api = UpbitAPI()
        self.current_ticker = "KRW-BTC"
        self.current_interval = "minute5"
        self.current_data = None  # 현재 차트 데이터 저장
        
        # 자동 새로고침 타이머
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 1  # 초 (기본값)
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.auto_refresh_chart)
        
        # WebSocket (현재가 업데이트용)
        self.ws_current_price = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 툴바
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 수직 스플리터 (차트 + AI 패널)
        splitter = QSplitter(Qt.Vertical)
        
        # 메인 차트
        self.figure = Figure(figsize=(10, 7), facecolor='#1e2329')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #1e2329;")
        splitter.addWidget(self.canvas)
        
        # AI 예측 패널
        ai_panel = self.create_ai_panel()
        splitter.addWidget(ai_panel)
        
        splitter.setSizes([600, 150])
        layout.addWidget(splitter)
        
        # 초기 차트 로드
        self.update_chart(self.current_ticker, self.current_interval)
        
        # 자동 새로고침 시작
        if self.auto_refresh_enabled:
            self.start_auto_refresh()
        
    def create_toolbar(self):
        """차트 툴바"""
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #2b3139;
                border-bottom: 1px solid #474d57;
            }
        """)
        toolbar.setFixedHeight(45)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 현재 티커 표시
        self.ticker_label = QLabel("BTC/KRW")
        self.ticker_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #fcd535;
            padding-right: 15px;
        """)
        layout.addWidget(self.ticker_label)
        
        # 시간 간격 버튼들
        self.interval_buttons = {}
        intervals = [
            ('1분', 'minute1'),
            ('5분', 'minute5'),
            ('15분', 'minute15'),
            ('1시간', 'minute60'),
            ('1일', 'day')
        ]
        
        for label, interval in intervals:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #474d57;
                    border-radius: 4px;
                    padding: 5px 12px;
                    color: #b7bdc6;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                    color: #fcd535;
                }
            """)
            btn.clicked.connect(lambda checked, i=interval: self.change_interval(i))
            self.interval_buttons[interval] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 지표 버튼
        self.show_ma = True
        ma_btn = QPushButton("MA")
        ma_btn.setCheckable(True)
        ma_btn.setChecked(True)
        ma_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b3139;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 5px 10px;
                color: #b7bdc6;
            }
            QPushButton:checked {
                background-color: #1fc7d4;
                color: white;
                border: none;
            }
        """)
        ma_btn.clicked.connect(lambda: self.toggle_ma(ma_btn.isChecked()))
        layout.addWidget(ma_btn)
        
        # 자동 갱신 체크박스
        self.auto_refresh_checkbox = QCheckBox("자동갱신")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.setStyleSheet("""
            QCheckBox {
                color: #b7bdc6;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #1fc7d4;
                border: 1px solid #1fc7d4;
            }
        """)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_checkbox)
        
        # 갱신 간격 선택
        interval_label = QLabel("간격:")
        interval_label.setStyleSheet("color: #b7bdc6; padding-right: 5px;")
        layout.addWidget(interval_label)
        
        self.refresh_interval_combo = QComboBox()
        self.refresh_interval_combo.addItems(["1초", "3초", "5초", "10초", "30초", "60초"])
        self.refresh_interval_combo.setCurrentText("1초")  # 기본값
        self.refresh_interval_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b3139;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 5px 10px;
                color: #b7bdc6;
                min-width: 60px;
            }
            QComboBox:hover {
                border-color: #1fc7d4;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.refresh_interval_combo.currentTextChanged.connect(self.change_refresh_interval)
        layout.addWidget(self.refresh_interval_combo)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #fcd535;
                color: #1e2329;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0b90b;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_chart)
        layout.addWidget(refresh_btn)
        
        return toolbar
        
    def create_ai_panel(self):
        """AI 예측 패널"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #2b3139;")
        panel.setFixedHeight(150)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 현재가 정보
        self.info_label = QLabel("현재가: 로딩중...")
        self.info_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        return panel
        
    def update_ticker(self, ticker):
        """티커 변경"""
        self.current_ticker = ticker
        symbol = ticker.split('-')[1] if '-' in ticker else ticker
        self.ticker_label.setText(f"{symbol}/KRW")
        self.update_chart(ticker, self.current_interval)
        
    def change_interval(self, interval):
        """시간 간격 변경"""
        self.current_interval = interval
        self.update_chart(self.current_ticker, interval)
    
    def toggle_ma(self, checked):
        """이동평균선 토글"""
        self.show_ma = checked
        self.update_chart(self.current_ticker, self.current_interval)
        
    def refresh_chart(self):
        """차트 새로고침"""
        self.update_chart(self.current_ticker, self.current_interval)
    
    def toggle_auto_refresh(self, state):
        """자동 새로고침 토글"""
        self.auto_refresh_enabled = (state == 2)  # Qt.Checked = 2
        
        if self.auto_refresh_enabled:
            self.start_auto_refresh()
            print(f"✅ 자동 새로고침 활성화 ({self.auto_refresh_interval}초)")
        else:
            self.stop_auto_refresh()
            print("⏸️ 자동 새로고침 비활성화")
    
    def change_refresh_interval(self, text):
        """갱신 간격 변경"""
        interval_map = {
            "1초": 1,
            "3초": 3,
            "5초": 5,
            "10초": 10,
            "30초": 30,
            "60초": 60
        }
        self.auto_refresh_interval = interval_map.get(text, 5)
        
        # 타이머 재시작
        if self.auto_refresh_enabled:
            self.stop_auto_refresh()
            self.start_auto_refresh()
            print(f"⏱️ 갱신 간격 변경: {self.auto_refresh_interval}초")
    
    def start_auto_refresh(self):
        """자동 새로고침 시작"""
        if not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start(self.auto_refresh_interval * 1000)
    
    def stop_auto_refresh(self):
        """자동 새로고침 중지"""
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
    
    def auto_refresh_chart(self):
        """타이머에 의한 자동 새로고침"""
        if self.auto_refresh_enabled:
            self.refresh_chart()
        
    def update_chart(self, ticker, interval):
        """차트 업데이트"""
        try:
            # 데이터 가져오기 (캐싱 사용)
            df = self.api.get_ohlcv(ticker, interval=interval, count=200, use_cache=True)
            
            if df is None or df.empty:
                self.plot_error_message("데이터를 불러올 수 없습니다")
                return
            
            # 현재 데이터 저장 (다음 갱신 시 비교용)
            self.current_data = df
            
            # 현재가 정보 업데이트
            current_price = df.iloc[-1]['close']
            prev_close = df.iloc[-2]['close'] if len(df) > 1 else current_price
            change = ((current_price - prev_close) / prev_close) * 100
            
            change_text = f"{change:+.2f}%"
            change_color = "#f6465d" if change >= 0 else "#1fc7d4"
            
            self.info_label.setText(
                f"현재가: <span style='color: {change_color};'>₩{current_price:,.0f}</span> "
                f"<span style='color: {change_color};'>({change_text})</span>"
            )
            
            # mplfinance로 전문적인 차트 그리기
            self.plot_professional_chart(df, ticker)
            
        except Exception as e:
            print(f"차트 업데이트 에러: {e}")
            import traceback
            traceback.print_exc()
            self.plot_error_message(f"에러: {str(e)}")
            
    def plot_professional_chart(self, df, ticker):
        """업비트 스타일 전문 차트"""
        # 업비트 스타일 설정
        mc = mpf.make_marketcolors(
            up='#f6465d',    # 상승 캔들 (빨강)
            down='#1fc7d4',  # 하락 캔들 (청록)
            edge='inherit',
            wick='inherit',
            volume='in',
            alpha=0.9
        )
        
        s = mpf.make_mpf_style(
            marketcolors=mc,
            figcolor='#1e2329',
            facecolor='#1e2329',
            edgecolor='#474d57',
            gridcolor='#2b3139',
            gridstyle='--',
            gridaxis='both',
            y_on_right=True,
            rc={
                'axes.labelcolor': '#b7bdc6',
                'xtick.color': '#b7bdc6',
                'ytick.color': '#b7bdc6',
                'axes.edgecolor': '#474d57',
                'grid.alpha': 0.3,
                'font.size': 9,
            }
        )
        
        # 이동평균선 추가 (선택적)
        addplot = None
        if self.show_ma:
            # MA5, MA20, MA60
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['MA60'] = df['close'].rolling(window=60).mean()
            
            addplot = [
                mpf.make_addplot(df['MA5'], color='#9c27b0', width=1, alpha=0.6),   # 보라색
                mpf.make_addplot(df['MA20'], color='#ff9800', width=1, alpha=0.6),  # 주황색
                mpf.make_addplot(df['MA60'], color='#4caf50', width=1, alpha=0.6),  # 초록색
            ]
        
        # 차트 그리기
        symbol = ticker.split('-')[1] if '-' in ticker else ticker
        
        # 기존 figure의 참조 저장 및 정리
        old_fig = self.canvas.figure
        
        # mplfinance로 새 figure 생성
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=s,
            volume=True,
            addplot=addplot,
            title=f'{symbol}/KRW',
            ylabel='',
            ylabel_lower='Volume',
            figsize=(10, 7),
            panel_ratios=(3, 1),
            datetime_format='%m/%d %H:%M',
            xrotation=0,
            returnfig=True,  # Figure 반환
            show_nontrading=False,
            warn_too_much_data=300
        )
        
        # Canvas에 새 figure 설정
        self.canvas.figure = fig
        self.canvas.draw()
        
        # 이전 figure 정리 (메모리 누수 방지)
        if old_fig is not None and old_fig != fig:
            plt.close(old_fig)
        
    def plot_error_message(self, message):
        """에러 메시지 표시"""
        self.figure.clf()
        ax = self.figure.add_subplot(111, facecolor='#1e2329')
        ax.text(0.5, 0.5, message, 
                ha='center', va='center',
                color='#f6465d', fontsize=14,
                transform=ax.transAxes)
        ax.axis('off')
        self.canvas.draw()
