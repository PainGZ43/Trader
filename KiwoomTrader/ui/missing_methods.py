
    # Watchlist Management Methods
    def init_watchlist(self):
        """관심종목 탭 초기화"""
        layout = QVBoxLayout()
        
        # 상단 컨트롤
        control_layout = QHBoxLayout()
        
        self.watchlist_code_input = QLineEdit()
        self.watchlist_code_input.setPlaceholderText("종목 코드 (예: 005930)")
        self.watchlist_code_input.returnPressed.connect(self.add_to_watchlist)
        
        self.watchlist_name_input = QLineEdit()
        self.watchlist_name_input.setPlaceholderText("종목명 (선택)")
        self.watchlist_name_input.returnPressed.connect(self.add_to_watchlist)
        
        add_btn = QPushButton("➕ 추가")
        add_btn.clicked.connect(self.add_to_watchlist)
        add_btn.setStyleSheet("background-color: #00b894; color: white;")
        
        remove_btn = QPushButton("➖ 제거")
        remove_btn.clicked.connect(self.remove_from_watchlist)
        remove_btn.setStyleSheet("background-color: #d63031; color: white;")
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.load_watchlist)
        
        control_layout.addWidget(QLabel("종목:"))
        control_layout.addWidget(self.watchlist_code_input)
        control_layout.addWidget(self.watchlist_name_input)
        control_layout.addWidget(add_btn)
        control_layout.addWidget(remove_btn)
        control_layout.addWidget(refresh_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 관심종목 테이블
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(3)
        self.watchlist_table.setHorizontalHeaderLabels(["종목코드", "종목명", "현재가"])
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.watchlist_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.watchlist_table)
        
        self.tab_watchlist.setLayout(layout)

    def add_to_watchlist(self):
        """관심종목 추가"""
        code = self.watchlist_code_input.text().strip()
        name = self.watchlist_name_input.text().strip()
        
        if not code:
            self.log("종목 코드를 입력하세요")
            return
        
        if self.watchlist_manager.add(code, name):
            self.log(f"✅ {code} 관심종목에 추가")
            self.watchlist_code_input.clear()
            self.watchlist_name_input.clear()
            self.load_watchlist()
        else:
            self.log(f"⚠️ {code}는 이미 관심종목에 있습니다")

    def remove_from_watchlist(self):
        """관심종목 제거"""
        selected = self.watchlist_table.selectedItems()
        if not selected:
            self.log("제거할 종목을 선택하세요")
            return
        
        row = selected[0].row()
        code = self.watchlist_table.item(row, 0).text()
        
        if self.watchlist_manager.remove(code):
            self.log(f"🗑️ {code} 관심종목에서 제거")
            self.load_watchlist()
        else:
            self.log(f"❌ {code} 제거 실패")

    def load_watchlist(self):
        """관심종목 로드 및 표시"""
        stocks = self.watchlist_manager.get_all()
        
        self.watchlist_table.setRowCount(len(stocks))
        
        for i, stock in enumerate(stocks):
            self.watchlist_table.setItem(i, 0, QTableWidgetItem(stock['code']))
            self.watchlist_table.setItem(i, 1, QTableWidgetItem(stock.get('name', '-')))
            self.watchlist_table.setItem(i, 2, QTableWidgetItem('-'))  # 현재가는 나중에 업데이트
        
        self.log(f"📋 관심종목 {len(stocks)}개 로드 완료")

    # AI Recommendations Methods
    def init_recommend(self):
        """AI 추천 탭 초기화"""
        layout = QVBoxLayout()
        
        # 설명
        desc_label = QLabel(
            "AI가 관심종목을 분석하여 매수 타이밍이 좋은 종목을 추천합니다.\n"
            "AI 점수 + 감성분석 + 기술적 지표를 종합하여 평가합니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b2bec3; font-size: 12px; padding: 10px;")
        layout.addWidget(desc_label)
        
        # 분석 버튼
        btn_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🎯 관심종목 분석 시작")
        self.analyze_btn.clicked.connect(self.analyze_watchlist)
        self.analyze_btn.setStyleSheet("background-color: #6c5ce7; color: white; padding: 10px; font-weight: bold;")
        
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 진행 바
        self.recommend_progress = QProgressBar()
        self.recommend_progress.setRange(0, 100)
        self.recommend_progress.setValue(0)
        self.recommend_progress.setVisible(False)
        layout.addWidget(self.recommend_progress)
        
        # 추천 결과 테이블
        self.recommend_table = QTableWidget()
        self.recommend_table.setColumnCount(7)
        self.recommend_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "현재가", "AI점수", "감성", "기술", "추천"
        ])
        self.recommend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.recommend_table)
        
        self.tab_recommend.setLayout(layout)

    def analyze_watchlist(self):
        """관심종목 AI 분석"""
        stocks = self.watchlist_manager.get_all()
        
        if not stocks:
            self.log("분석할 관심종목이 없습니다")
            return
        
        self.log(f"🎯 {len(stocks)}개 종목 AI 분석 시작...")
        self.analyze_btn.setEnabled(False)
        self.recommend_progress.setVisible(True)
        self.recommend_progress.setValue(0)
        
        def analyze_thread():
            def update_progress(current, total):
                pct = int((current / total) * 100)
                self.recommend_progress.setValue(pct)
                QApplication.processEvents()
            
            try:
                results = self.recommender.analyze_stocks(
                    [s['code'] for s in stocks],
                    progress_callback=update_progress
                )
                
                self.recommend_progress.setValue(100)
                self.display_recommendations(results)
                self.log(f"✅ AI 분석 완료: {len(results)}개 종목")
            except Exception as e:
                self.log(f"❌ AI 분석 실패: {str(e)}")
            finally:
                self.analyze_btn.setEnabled(True)
                self.recommend_progress.setVisible(False)
        
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()

    def display_recommendations(self, results):
        """추천 결과 표시"""
        self.recommend_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # 종목코드
            self.recommend_table.setItem(i, 0, QTableWidgetItem(result['code']))
            
            # 종목명 (관심종목에서 가져오기)
            stocks = self.watchlist_manager.get_all()
            name = next((s['name'] for s in stocks if s['code'] == result['code']), '-')
            self.recommend_table.setItem(i, 1, QTableWidgetItem(name))
            
            # 현재가
            self.recommend_table.setItem(i, 2, QTableWidgetItem(f"{result.get('price', 0):,.0f}"))
            
            # AI점수
            ai_item = QTableWidgetItem(f"{result['ai_score']:.2f}")
            ai_item.setForeground(QColor("#74b9ff"))
            self.recommend_table.setItem(i, 3, ai_item)
            
            # 감성
            sent_item = QTableWidgetItem(f"{result['sentiment_score']:.2f}")
            self.recommend_table.setItem(i, 4, sent_item)
            
            # 기술
            tech_item = QTableWidgetItem(f"{result['technical_score']:.2f}")
            self.recommend_table.setItem(i, 5, tech_item)
            
            # 추천 등급
            rec_item = QTableWidgetItem(f"{result['grade']} - {result['recommendation']}")
            rec_item.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            
            if result['grade'] == 'A':
                rec_item.setForeground(QColor("#00b894"))
            elif result['grade'] == 'B':
                rec_item.setForeground(QColor("#74b9ff"))
            elif result['grade'] in ['D', 'F']:
                rec_item.setForeground(QColor("#d63031"))
            
            self.recommend_table.setItem(i, 6, rec_item)

    # Settings Methods
    def init_settings(self):
        """설정 탭 초기화 - AI 학습 포함"""
        layout = QVBoxLayout()
        
        # AI 학습 섹션
        ai_train_group = QGroupBox("🤖 AI 모델 학습")
        ai_train_layout = QVBoxLayout()
        
        # 설명
        desc_label = QLabel(
            "고급 AI 모델(LSTM + XGBoost)을 학습합니다.\n"
            "실제 과거 데이터를 다운로드하여 학습하므로 10-15분 정도 소요됩니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b2bec3; font-size: 12px;")
        ai_train_layout.addWidget(desc_label)
        
        # 학습 설정
        settings_layout = QFormLayout()
        
        self.train_code_input = QLineEdit("005930")
        self.train_code_input.setPlaceholderText("종목 코드 (예: 005930)")
        
        self.train_interval_combo = QComboBox()
        self.train_interval_combo.addItems(["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"])
        self.train_interval_combo.setCurrentText("1h")
        self.train_interval_combo.setToolTip("1h 권장 (1m은 데이터가 너무 많음)")
        self.train_interval_combo.currentTextChanged.connect(self.on_interval_changed)
        
        self.train_period_combo = QComboBox()
        self.train_period_combo.currentTextChanged.connect(self.update_estimated_time)
        
        self.use_gpu_check = QCheckBox("GPU 사용 (Use GPU)")
        self.use_gpu_check.setChecked(False)
        self.use_gpu_check.stateChanged.connect(self.update_estimated_time)
        
        self.estimated_time_label = QLabel("예상 소요 시간: 계산 중...")
        self.estimated_time_label.setStyleSheet("color: #fdcb6e; font-style: italic;")
        
        # Trigger initial update
        self.on_interval_changed(self.train_interval_combo.currentText())
        
        settings_layout.addRow("종목 코드:", self.train_code_input)
        settings_layout.addRow("데이터 간격:", self.train_interval_combo)
        settings_layout.addRow("학습 기간:", self.train_period_combo)
        settings_layout.addRow("", self.use_gpu_check)
        settings_layout.addRow("", self.estimated_time_label)
        
        ai_train_layout.addLayout(settings_layout)
        
        # 학습 버튼
        button_layout = QHBoxLayout()
        
        self.train_start_btn = QPushButton("🚀 학습 시작")
        self.train_start_btn.setStyleSheet("background-color: #00b894; color: white; font-weight: bold; padding: 10px;")
        self.train_start_btn.clicked.connect(self.start_ai_training)
        
        self.train_stop_btn = QPushButton("⏹️ 중지")
        self.train_stop_btn.setStyleSheet("background-color: #d63031; color: white; padding: 10px;")
        self.train_stop_btn.setEnabled(False)
        self.train_stop_btn.clicked.connect(self.cancel_training)
        
        button_layout.addWidget(self.train_start_btn)
        button_layout.addWidget(self.train_stop_btn)
        button_layout.addStretch()
        
        ai_train_layout.addLayout(button_layout)
        
        # 진행률 표시
        self.train_progress = QProgressBar()
        self.train_progress.setRange(0, 100)
        self.train_progress.setValue(0)
        self.train_progress.setVisible(False)
        ai_train_layout.addWidget(self.train_progress)
        
        # 결과 표시
        self.train_result_text = QTextEdit()
        self.train_result_text.setReadOnly(True)
        self.train_result_text.setMaximumHeight(200)
        ai_train_layout.addWidget(self.train_result_text)
        
        ai_train_group.setLayout(ai_train_layout)
        layout.addWidget(ai_train_group)
        
        # 일반 설정 섹션
        general_group = QGroupBox("⚙️ 일반 설정")
        general_layout = QFormLayout()
        
        # Settings Button
        self.open_settings_btn = QPushButton("🛠️ API 및 계좌 설정")
        self.open_settings_btn.clicked.connect(self.open_settings_dialog)
        self.open_settings_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        
        general_layout.addRow(self.open_settings_btn)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        layout.addStretch()
        self.tab_settings.setLayout(layout)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.log("설정이 저장되었습니다. 일부 변경사항은 재시작 후 적용됩니다.")

    def on_interval_changed(self, interval):
        """데이터 간격 변경 시 학습 기간 옵션 자동 조정"""
        self.train_period_combo.blockSignals(True)
        self.train_period_combo.clear()
        
        periods = []
        default_period = ""
        
        if interval == "1m":
            periods = ["1d", "5d"]
            default_period = "5d"
        elif interval in ["2m", "5m", "15m", "30m", "90m"]:
            periods = ["1d", "5d", "1mo"]
            default_period = "1mo"
        elif interval in ["60m", "1h"]:
            periods = ["1mo", "3mo", "6mo", "1y", "2y"]
            default_period = "1y"
        else:
            periods = ["6mo", "1y", "2y", "5y", "10y", "max"]
            default_period = "5y"
            
        self.train_period_combo.addItems(periods)
        self.train_period_combo.setCurrentText(default_period)
        self.train_period_combo.blockSignals(False)
        
        self.update_estimated_time()

    def update_estimated_time(self):
        """예상 학습 시간 계산"""
        period = self.train_period_combo.currentText()
        interval = self.train_interval_combo.currentText()
        use_gpu = self.use_gpu_check.isChecked()
        
        # Base time in minutes
        base_time = 5 
        
        # Period factor
        if period == "1mo": factor = 0.2
        elif period == "3mo": factor = 0.5
        elif period == "6mo": factor = 0.8
        elif period == "1y": factor = 1.0
        elif period == "2y": factor = 1.8
        elif period == "5y": factor = 4.0
        else: factor = 1.0
        
        # Interval factor
        if interval == "1m": factor *= 10.0
        elif interval == "5m": factor *= 3.0
        elif interval == "30m": factor *= 1.5
        elif interval == "1h": factor *= 1.0
        elif interval == "1d": factor *= 0.2
        else: factor *= 1.0
        
        est_minutes = base_time * factor
        
        if use_gpu:
            est_minutes *= 0.4
            
        self.estimated_time_label.setText(f"예상 소요 시간: 약 {est_minutes:.1f} 분")

    def start_ai_training(self):
        """AI 모델 학습 시작"""
        self.training_cancel_flag = False
        
        # UI 잠금
        self.train_start_btn.setEnabled(False)
        self.train_stop_btn.setEnabled(True)
        self.train_progress.setVisible(True)
        self.train_progress.setValue(0)
        self.train_result_text.clear()
        
        # 파라미터 가져오기
        stock_code = self.train_code_input.text()
        period = self.train_period_combo.currentText()
        interval = self.train_interval_combo.currentText()
        use_gpu = self.use_gpu_check.isChecked()
        
        def train_thread():
            try:
                from ai.data_collector import DataCollector
                from ai.indicators import IndicatorCalculator
                from ai.lstm_model import LSTMPredictor, TENSORFLOW_AVAILABLE
                from ai.xgboost_model import XGBoostPredictor
                
                self.train_progress.setValue(5)
                self.train_result_text.append("[1/4] 데이터 다운로드 중...")
                QApplication.processEvents()
                
                collector = DataCollector()
                yf_symbol = DataCollector.convert_korean_code(stock_code)
                df = collector.get_stock_data(yf_symbol, period=period, interval=interval, use_cache=False)
                
                if self.training_cancel_flag:
                    self.train_result_text.append("❌ 학습이 중단되었습니다\n")
                    self._finish_training(False)
                    return
                
                if df is None or len(df) < 1000:
                    self.train_result_text.append("❌ 데이터 부족\n")
                    self._finish_training(False)
                    return
                
                self.train_progress.setValue(20)
                self.train_result_text.append(f"✓ {len(df)}개 데이터 다운로드 완료\n")
                self.train_result_text.append("[2/4] 기술적 지표 계산 중...")
                QApplication.processEvents()
                
                df = IndicatorCalculator.calculate_all(df)
                df = df.dropna()
                
                if self.training_cancel_flag:
                    self.train_result_text.append("❌ 학습이 중단되었습니다\n")
                    self._finish_training(False)
                    return
                
                self.train_progress.setValue(40)
                self.train_result_text.append("✓ 지표 계산 완료\n")
                QApplication.processEvents()
                
                # LSTM 학습
                self.train_result_text.append("[3/4] LSTM 모델 학습 중...")
                QApplication.processEvents()
                
                lookback = 100
                X_lstm, y_lstm, scaler = collector.prepare_training_data(df, lookback=lookback)
                
                if TENSORFLOW_AVAILABLE:
                    lstm_model = LSTMPredictor(lookback=lookback, n_features=X_lstm.shape[2])
                    lstm_model.train(X_lstm, y_lstm, epochs=30, batch_size=32)
                    self.train_progress.setValue(60)
                    self.train_result_text.append("✓ LSTM 학습 완료\n")
                else:
                    self.train_result_text.append("⚠️ TensorFlow 미사용, LSTM 스킵\n")
                
                if self.training_cancel_flag:
                    self.train_result_text.append("❌ 학습이 중단되었습니다\n")
                    self._finish_training(False)
                    return
                
                collector.save_scaler(scaler, 'models/scaler.pkl')
                
                # XGBoost 학습
                self.train_result_text.append("[4/4] XGBoost 모델 학습 중...")
                QApplication.processEvents()
                
                feature_cols = IndicatorCalculator.get_feature_names()
                X_xgb = df[feature_cols].values
                y_xgb = (df['close'].shift(-1) > df['close']).astype(int).values
                
                mask = ~np.isnan(y_xgb)
                X_xgb = X_xgb[mask]
                y_xgb = y_xgb[mask]
                
                self.train_progress.setValue(70)
                QApplication.processEvents()
                
                xgboost_model = XGBoostPredictor()
                xgb_metrics = xgboost_model.train(X_xgb, y_xgb)
                
                self.train_progress.setValue(90)
                self.train_result_text.append("✓ XGBoost 학습 완료\n")
                QApplication.processEvents()
                
                # 완료
                self.train_progress.setValue(100)
                self.train_result_text.append("\n" + "="*50)
                self.train_result_text.append("\n✅ AI 학습 완료!")
                self.train_result_text.append(f"\nXGBoost 정확도: {xgb_metrics['accuracy']:.2%}")
                self.train_result_text.append(f"\nAUC: {xgb_metrics['auc']:.2%}\n")
                self.train_result_text.append(f"\n모델 저장 위치:\n")
                self.train_result_text.append(f"  - models/xgboost_model.pkl\n")
                self.train_result_text.append(f"  - models/scaler.pkl\n")
                
                self.log(f"✅ AI 학습 완료: 정확도 {xgb_metrics['accuracy']:.2%}")
                
                QMessageBox.information(
                    self,
                    "학습 완료",
                    f"✅ AI 모델 학습이 완료되었습니다!\n\n"
                    f"XGBoost 정확도: {xgb_metrics['accuracy']:.2%}\n"
                    f"AUC: {xgb_metrics['auc']:.2%}\n\n"
                    f"모델이 저장되었습니다."
                )
                
                self._finish_training(True)
                
            except Exception as e:
                self.train_result_text.append(f"\n❌ 오류 발생: {str(e)}\n")
                self.log(f"❌ AI 학습 실패: {str(e)}")
                self._finish_training(False)
        
        thread = threading.Thread(target=train_thread, daemon=True)
        thread.start()

    def cancel_training(self):
        """AI 학습 중단"""
        self.training_cancel_flag = True
        self.train_stop_btn.setEnabled(False)
        self.train_result_text.append("\n⏹️ 학습 중단 중...\n")
        self.log("⏹️ AI 학습 중단 요청")
    
    def _finish_training(self, success):
        """학습 완료 후 UI 복원"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        if not success:
            self.train_progress.setVisible(False)
        self.training_cancel_flag = False


# Settings Dialog Class
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # API Settings
        api_group = QGroupBox("키움 API 설정")
        api_layout = QFormLayout()
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.account_input = QLineEdit()
        
        api_layout.addRow("App Key:", self.app_key_input)
        api_layout.addRow("Secret Key:", self.secret_key_input)
        api_layout.addRow("계좌번호:", self.account_input)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["모의투자", "실전투자"])
        api_layout.addRow("모드:", self.mode_combo)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # KakaoTalk Settings
        kakao_group = QGroupBox("카카오톡 알림 설정")
        kakao_layout = QFormLayout()
        
        self.kakao_access_input = QLineEdit()
        self.kakao_refresh_input = QLineEdit()
        
        kakao_layout.addRow("Access Token:", self.kakao_access_input)
        kakao_layout.addRow("Refresh Token:", self.kakao_refresh_input)
        
        kakao_group.setLayout(kakao_layout)
        layout.addWidget(kakao_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_settings(self):
        self.app_key_input.setText(settings.get("APP_KEY", ""))
        self.secret_key_input.setText(settings.get("SECRET_KEY", ""))
        self.account_input.setText(settings.get("ACCOUNT_NO", ""))
        self.kakao_access_input.setText(settings.get("KAKAO_ACCESS_TOKEN", ""))
        self.kakao_refresh_input.setText(settings.get("KAKAO_REFRESH_TOKEN", ""))
        
        is_virtual = settings.get("IS_VIRTUAL", True)
        self.mode_combo.setCurrentIndex(0 if is_virtual else 1)

    def save_settings(self):
        new_settings = {
            "APP_KEY": self.app_key_input.text().strip(),
            "SECRET_KEY": self.secret_key_input.text().strip(),
            "ACCOUNT_NO": self.account_input.text().strip(),
            "KAKAO_ACCESS_TOKEN": self.kakao_access_input.text().strip(),
            "KAKAO_REFRESH_TOKEN": self.kakao_refresh_input.text().strip(),
            "IS_VIRTUAL": self.mode_combo.currentIndex() == 0
        }
        settings.save_settings(new_settings)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        self.accept()
