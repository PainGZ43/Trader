# Enhanced Settings Dialog - 모든 설정을 UI로!

# 기존 Settings Dialog를 대체할 확장 버전
# 추가 기능:
# - 전략 파라미터
# - 리스크 관리
# - 알림 설정
# - 고급 옵션

class EnhancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("전체 설정")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 탭 위젯으로 설정 구분
        tab_widget = QTabWidget()
        
        # Tab 1: API 설정
        api_tab = QWidget()
        api_layout = QVBoxLayout()
        
        ##키움 API
        api_group = QGroupBox("키움 API 설정")
        api_form = QFormLayout()
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.account_input = QLineEdit()
        
        api_form.addRow("App Key:", self.app_key_input)
        api_form.addRow("Secret Key:", self.secret_key_input)
        api_form.addRow("계좌번호:", self.account_input)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["모의투자", "실전투자"])
        api_form.addRow("모드:", self.mode_combo)
        
        api_group.setLayout(api_form)
        api_layout.addWidget(api_group)
        
        # 카카오톡
        kakao_group = QGroupBox("카카오톡 알림")
        kakao_form = QFormLayout()
        
        self.kakao_access_input = QLineEdit()
        self.kakao_refresh_input = QLineEdit()
        
        kakao_form.addRow("Access Token:", self.kakao_access_input)
        kakao_form.addRow("Refresh Token:", self.kakao_refresh_input)
        
        kakao_group.setLayout(kakao_form)
        api_layout.addWidget(kakao_group)
        
        api_layout.addStretch()
        api_tab.setLayout(api_layout)
        
        # Tab 2: 전략 파라미터
        strategy_tab = QWidget()
        strategy_layout = QVBoxLayout()
        
        strat_group = QGroupBox("📊 매매 전략 파라미터")
        strat_form = QFormLayout()
        
        # 볼륨 임계값
        self.vol_threshold_spin = QDoubleSpinBox()
        self.vol_threshold_spin.setRange(0.5, 5.0)
        self.vol_threshold_spin.setSingleStep(0.1)
        self.vol_threshold_spin.setValue(1.5)
        self.vol_threshold_spin.setSuffix("x")
        strat_form.addRow("볼륨 임계값:", self.vol_threshold_spin)
        
        # AI 점수 임계값
        self.ai_threshold_spin = QDoubleSpinBox()
        self.ai_threshold_spin.setRange(0.0, 1.0)
        self.ai_threshold_spin.setSingleStep(0.05)
        self.ai_threshold_spin.setValue(0.6)
        strat_form.addRow("AI 점수 임계값:", self.ai_threshold_spin)
        
        # 익절 목표
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(0.5, 20.0)
        self.take_profit_spin.setSingleStep(0.5)
        self.take_profit_spin.setValue(3.0)
        self.take_profit_spin.setSuffix("%")
        strat_form.addRow("익절 목표:", self.take_profit_spin)
        
        # 손절 목표
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.5, 10.0)
        self.stop_loss_spin.setSingleStep(0.5)
        self.stop_loss_spin.setValue(2.0)
        self.stop_loss_spin.setSuffix("%")
        strat_form.addRow("손절 목표:", self.stop_loss_spin)
        
        # 쿨다운
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 120)
        self.cooldown_spin.setValue(15)
        self.cooldown_spin.setSuffix(" 분")
        strat_form.addRow("쿨다운 시간:", self.cooldown_spin)
        
        strat_group.setLayout(strat_form)
        strategy_layout.addWidget(strat_group)
        
        strategy_layout.addStretch()
        strategy_tab.setLayout(strategy_layout)
        
        # Tab 3: 리스크 관리
        risk_tab = QWidget()
        risk_layout = QVBoxLayout()
        
        risk_group = QGroupBox("⚠️ 리스크 관리")
        risk_form = QFormLayout()
        
        # 최대 보유 종목
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(5)
        risk_form.addRow("최대 보유 종목:", self.max_positions_spin)
        
        # 종목당 최대 비중
        self.max_position_size_spin = QDoubleSpinBox()
        self.max_position_size_spin.setRange(1.0, 100.0)
        self.max_position_size_spin.setSingleStep(1.0)
        self.max_position_size_spin.setValue(20.0)
        self.max_position_size_spin.setSuffix("%")
        risk_form.addRow("종목당 최대 비중:", self.max_position_size_spin)
        
        # 일일 최대 손실
        self.daily_loss_limit_spin = QDoubleSpinBox()
        self.daily_loss_limit_spin.setRange(1.0, 20.0)
        self.daily_loss_limit_spin.setSingleStep(0.5)
        self.daily_loss_limit_spin.setValue(5.0)
        self.daily_loss_limit_spin.setSuffix("%")
        risk_form.addRow("일일 최대 손실:", self.daily_loss_limit_spin)
        
        # 최소 매수 금액
        self.min_buy_amount_spin = QSpinBox()
        self.min_buy_amount_spin.setRange(10000, 10000000)
        self.min_buy_amount_spin.setSingleStep(10000)
        self.min_buy_amount_spin.setValue(100000)
        risk_form.addRow("최소 매수 금액:", self.min_buy_amount_spin)
        
        risk_group.setLayout(risk_form)
        risk_layout.addWidget(risk_group)
        
        risk_layout.addStretch()
        risk_tab.setLayout(risk_layout)
        
        # Tab 4: 알림 설정
        notification_tab = QWidget()
        notif_layout = QVBoxLayout()
        
        notif_group = QGroupBox("🔔 알림 설정")
        notif_form = QFormLayout()
       
        # 매매 알림
        self.notify_trade_check = QCheckBox("매매 체결 시 알림")
        self.notify_trade_check.setChecked(True)
        notif_form.addRow("", self.notify_trade_check)
        
        # 손익 알림
        self.notify_profit_check = QCheckBox("목표 손익 달성 시 알림")
        self.notify_profit_check.setChecked(True)
        notif_form.addRow("", self.notify_profit_check)
        
        # 일일 리포트
        self.daily_report_check = QCheckBox("일일 리포트 전송")
        self.daily_report_check.setChecked(True)
        notif_form.addRow("", self.daily_report_check)
        
        # 리포트 시간
        self.report_time_edit = QTimeEdit()
        self.report_time_edit.setTime(QTime(17, 0))
        notif_form.addRow("일일 리포트 시간:", self.report_time_edit)
        
        # 에러 알림
        self.notify_error_check = QCheckBox("에러 발생 시 알림")
        self.notify_error_check.setChecked(True)
        notif_form.addRow("", self.notify_error_check)
        
        notif_group.setLayout(notif_form)
        notif_layout.addWidget(notif_group)
        
        notif_layout.addStretch()
        notification_tab.setLayout(notif_layout)
        
        # Tab 5: 고급 설정
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout()
        
        adv_group = QGroupBox("🔧 고급 설정")
        adv_form = QFormLayout()
        
        # 업데이트 주기
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 60)
        self.update_interval_spin.setValue(5)
        self.update_interval_spin.setSuffix(" 초")
        adv_form.addRow("UI 업데이트 주기:", self.update_interval_spin)
        
        # 로깅 레벨
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        adv_form.addRow("로깅 레벨:", self.log_level_combo)
        
        # 데이터 캐싱
        self.enable_cache_check = QCheckBox("데이터 캐싱 사용")
        self.enable_cache_check.setChecked(True)
        adv_form.addRow("", self.enable_cache_check)
        
        # 자동 재연결
        self.auto_reconnect_check = QCheckBox("API 자동 재연결")
        self.auto_reconnect_check.setChecked(True)
        adv_form.addRow("", self.auto_reconnect_check)
        
        adv_group.setLayout(adv_form)
        advanced_layout.addWidget(adv_group)
        
        advanced_layout.addStretch()
        advanced_tab.setLayout(advanced_layout)
        
        # 탭 추가
        tab_widget.addTab(api_tab, "🔑 API")
        tab_widget.addTab(strategy_tab, "📊 전략")
        tab_widget.addTab(risk_tab, "⚠️ 리스크")
        tab_widget.addTab(notification_tab, "🔔 알림")
        tab_widget.addTab(advanced_tab, "🔧 고급")
        
        layout.addWidget(tab_widget)
        
        # 하단 버튼
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("기본값 복원")
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        save_btn = QPushButton("✅ 저장")
        save_btn.setStyleSheet("background-color: #00b894; color: white; padding: 10px; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def load_settings(self):
        """설정 불러오기"""
        # API 설정
        self.app_key_input.setText(settings.get("APP_KEY", ""))
        self.secret_key_input.setText(settings.get("SECRET_KEY", ""))
        self.account_input.setText(settings.get("ACCOUNT_NO", ""))
        self.kakao_access_input.setText(settings.get("KAKAO_ACCESS_TOKEN", ""))
        self.kakao_refresh_input.setText(settings.get("KAKAO_REFRESH_TOKEN", ""))
        
        is_virtual = settings.get("IS_VIRTUAL", True)
        self.mode_combo.setCurrentIndex(0 if is_virtual else 1)
        
        # 전략 파라미터
        self.vol_threshold_spin.setValue(settings.get("VOL_THRESHOLD", 1.5))
        self.ai_threshold_spin.setValue(settings.get("AI_THRESHOLD", 0.6))
        self.take_profit_spin.setValue(settings.get("TAKE_PROFIT", 3.0))
        self.stop_loss_spin.setValue(settings.get("STOP_LOSS", 2.0))
        self.cooldown_spin.setValue(settings.get("COOLDOWN", 15))
        
        # 리스크 관리
        self.max_positions_spin.setValue(settings.get("MAX_POSITIONS", 5))
        self.max_position_size_spin.setValue(settings.get("MAX_POSITION_SIZE", 20.0))
        self.daily_loss_limit_spin.setValue(settings.get("DAILY_LOSS_LIMIT", 5.0))
        self.min_buy_amount_spin.setValue(settings.get("MIN_BUY_AMOUNT", 100000))
        
        # 알림 설정
        self.notify_trade_check.setChecked(settings.get("NOTIFY_TRADE", True))
        self.notify_profit_check.setChecked(settings.get("NOTIFY_PROFIT", True))
        self.daily_report_check.setChecked(settings.get("DAILY_REPORT", True))
        
        report_time = settings.get("REPORT_TIME", "17:00")
        h, m = map(int, report_time.split(':'))
        self.report_time_edit.setTime(QTime(h, m))
        
        self.notify_error_check.setChecked(settings.get("NOTIFY_ERROR", True))
        
        # 고급 설정
        self.update_interval_spin.setValue(settings.get("UPDATE_INTERVAL", 5))
        self.log_level_combo.setCurrentText(settings.get("LOG_LEVEL", "INFO"))
        self.enable_cache_check.setChecked(settings.get("ENABLE_CACHE", True))
        self.auto_reconnect_check.setChecked(settings.get("AUTO_RECONNECT", True))

    def save_settings(self):
        """설정 저장"""
        new_settings = {
            # API
            "APP_KEY": self.app_key_input.text().strip(),
            "SECRET_KEY": self.secret_key_input.text().strip(),
            "ACCOUNT_NO": self.account_input.text().strip(),
            "KAKAO_ACCESS_TOKEN": self.kakao_access_input.text().strip(),
            "KAKAO_REFRESH_TOKEN": self.kakao_refresh_input.text().strip(),
            "IS_VIRTUAL": self.mode_combo.currentIndex() == 0,
            
            # 전략
            "VOL_THRESHOLD": self.vol_threshold_spin.value(),
            "AI_THRESHOLD": self.ai_threshold_spin.value(),
            "TAKE_PROFIT": self.take_profit_spin.value(),
            "STOP_LOSS": self.stop_loss_spin.value(),
            "COOLDOWN": self.cooldown_spin.value(),
            
            # 리스크
            "MAX_POSITIONS": self.max_positions_spin.value(),
            "MAX_POSITION_SIZE": self.max_position_size_spin.value(),
            "DAILY_LOSS_LIMIT": self.daily_loss_limit_spin.value(),
            "MIN_BUY_AMOUNT": self.min_buy_amount_spin.value(),
            
            # 알림
            "NOTIFY_TRADE": self.notify_trade_check.isChecked(),
            "NOTIFY_PROFIT": self.notify_profit_check.isChecked(),
            "DAILY_REPORT": self.daily_report_check.isChecked(),
            "REPORT_TIME": self.report_time_edit.time().toString("HH:mm"),
            "NOTIFY_ERROR": self.notify_error_check.isChecked(),
            
            # 고급
            "UPDATE_INTERVAL": self.update_interval_spin.value(),
            "LOG_LEVEL": self.log_level_combo.currentText(),
            "ENABLE_CACHE": self.enable_cache_check.isChecked(),
            "AUTO_RECONNECT": self.auto_reconnect_check.isChecked(),
        }
        
        settings.save_settings(new_settings)
        QMessageBox.information(self, "저장 완료", 
            "✅ 모든 설정이 저장되었습니다!\n\n"
            "일부 설정은 재시작 후 적용됩니다.")
        self.accept()

    def reset_to_defaults(self):
        """기본값으로 복원"""
        reply = QMessageBox.question(self, "기본값 복원",
            "모든 설정을 기본값으로 복원하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 전략
            self.vol_threshold_spin.setValue(1.5)
            self.ai_threshold_spin.setValue(0.6)
            self.take_profit_spin.setValue(3.0)
            self.stop_loss_spin.setValue(2.0)
            self.cooldown_spin.setValue(15)
            
            # 리스크
            self.max_positions_spin.setValue(5)
            self.max_position_size_spin.setValue(20.0)
            self.daily_loss_limit_spin.setValue(5.0)
            self.min_buy_amount_spin.setValue(100000)
            
            # 알림
            self.notify_trade_check.setChecked(True)
            self.notify_profit_check.setChecked(True)
            self.daily_report_check.setChecked(True)
            self.report_time_edit.setTime(QTime(17, 0))
            self.notify_error_check.setChecked(True)
            
            # 고급
            self.update_interval_spin.setValue(5)
            self.log_level_combo.setCurrentText("INFO")
            self.enable_cache_check.setChecked(True)
            self.auto_reconnect_check.setChecked(True)
            
            QMessageBox.information(self, "복원 완료", "기본값으로 복원되었습니다.")
