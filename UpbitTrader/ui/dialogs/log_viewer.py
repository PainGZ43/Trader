"""
로그 뷰어 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QCheckBox, QComboBox, QLabel,
                             QLineEdit, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
import os
from pathlib import Path


class LogViewerDialog(QDialog):
    """로그 뷰어 다이얼로그"""
    
    def __init__(self, log_file_path, parent=None):
        super().__init__(parent)
        self.log_file_path = Path(log_file_path)
        self.setWindowTitle("로그 뷰어")
        self.setMinimumSize(900, 600)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2329;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #2b3139;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            QPushButton {
                background-color: #2b3139;
                color: #ffffff;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3f47;
            }
            QPushButton#refreshButton {
                background-color: #0ecb81;
                border: none;
            }
            QPushButton#refreshButton:hover {
                background-color: #10d98f;
            }
            QPushButton#clearButton {
                background-color: #f6465d;
                border: none;
            }
            QPushButton#clearButton:hover {
                background-color: #f84960;
            }
            QCheckBox {
                color: #b7bdc6;
            }
            QComboBox, QLineEdit {
                background-color: #2b3139;
                color: #ffffff;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 6px;
            }
            QLabel {
                color: #b7bdc6;
            }
        """)
        
        # 자동 새로고침 타이머
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_logs)
        
        self.init_ui()
        self.load_logs()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 로그 레벨 필터
        control_layout.addWidget(QLabel("필터:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["전체", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentTextChanged.connect(self.apply_filter)
        control_layout.addWidget(self.level_filter)
        
        # 검색
        control_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력...")
        self.search_input.textChanged.connect(self.apply_filter)
        control_layout.addWidget(self.search_input)
        
        control_layout.addStretch()
        
        # 자동 새로고침
        self.auto_refresh_cb = QCheckBox("자동 새로고침 (3초)")
        self.auto_refresh_cb.stateChanged.connect(self.toggle_auto_refresh)
        control_layout.addWidget(self.auto_refresh_cb)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.load_logs)
        control_layout.addWidget(refresh_btn)
        
        # 로그 지우기 버튼
        clear_btn = QPushButton("🗑️ 로그 초기화")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_logs)
        control_layout.addWidget(clear_btn)
        
        layout.addLayout(control_layout)
        
        # 로그 내용 표시 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        
        # 폰트 설정
        font = QFont("Consolas", 10)
        self.log_text.setFont(font)
        
        layout.addWidget(self.log_text)
        
        # 정보 라벨
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #858585; font-size: 10px;")
        layout.addWidget(self.info_label)
        
        # 닫기 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def load_logs(self):
        """로그 파일 로드"""
        try:
            if not self.log_file_path.exists():
                self.log_text.setPlainText("로그 파일이 존재하지 않습니다.")
                self.info_label.setText("로그 파일이 없습니다.")
                return
            
            # 파일 크기 확인
            file_size = self.log_file_path.stat().st_size
            
            # 너무 큰 파일은 마지막 부분만 읽기 (1MB 제한)
            max_size = 1024 * 1024  # 1MB
            
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if file_size > max_size:
                    # 파일의 마지막 부분만 읽기
                    f.seek(max(0, file_size - max_size))
                    # 첫 줄은 불완전할 수 있으므로 건너뛰기
                    f.readline()
                    content = f.read()
                    self.full_log_content = content
                else:
                    content = f.read()
                    self.full_log_content = content
            
            # 필터 적용
            self.apply_filter()
            
            # 정보 업데이트
            lines = self.full_log_content.count('\n')
            size_kb = file_size / 1024
            self.info_label.setText(f"로그 파일: {self.log_file_path.name} | 크기: {size_kb:.1f} KB | 줄 수: {lines:,}")
            
        except Exception as e:
            self.log_text.setPlainText(f"로그 파일을 읽는 중 오류가 발생했습니다:\n{str(e)}")
            self.info_label.setText("오류 발생")
    
    def apply_filter(self):
        """필터 및 검색 적용"""
        if not hasattr(self, 'full_log_content'):
            return
        
        filtered_lines = []
        level_filter = self.level_filter.currentText()
        search_text = self.search_input.text().lower()
        
        for line in self.full_log_content.split('\n'):
            # 레벨 필터
            if level_filter != "전체":
                if level_filter not in line:
                    continue
            
            # 검색 필터
            if search_text and search_text not in line.lower():
                continue
            
            filtered_lines.append(line)
        
        # 색상 적용된 텍스트 생성
        colored_content = self.apply_color_formatting('\n'.join(filtered_lines))
        self.log_text.setHtml(colored_content)
        
        # 스크롤을 맨 아래로
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def apply_color_formatting(self, content):
        """로그 레벨에 따라 색상 적용"""
        lines = content.split('\n')
        colored_lines = []
        
        for line in lines:
            if 'ERROR' in line or 'CRITICAL' in line:
                colored_lines.append(f'<span style="color: #f6465d;">{self.escape_html(line)}</span>')
            elif 'WARNING' in line:
                colored_lines.append(f'<span style="color: #f0b90b;">{self.escape_html(line)}</span>')
            elif 'INFO' in line:
                colored_lines.append(f'<span style="color: #0ecb81;">{self.escape_html(line)}</span>')
            elif 'DEBUG' in line:
                colored_lines.append(f'<span style="color: #858585;">{self.escape_html(line)}</span>')
            else:
                colored_lines.append(f'<span style="color: #c9d1d9;">{self.escape_html(line)}</span>')
        
        return '<pre style="font-family: Consolas, Monaco, monospace; font-size: 11px;">' + '<br>'.join(colored_lines) + '</pre>'
    
    def escape_html(self, text):
        """HTML 특수 문자 이스케이프"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def toggle_auto_refresh(self, state):
        """자동 새로고침 토글"""
        if state == Qt.Checked:
            self.auto_refresh_timer.start(3000)  # 3초마다
        else:
            self.auto_refresh_timer.stop()
    
    def clear_logs(self):
        """로그 파일 초기화"""
        reply = QMessageBox.question(
            self,
            "로그 초기화 확인",
            "로그 파일을 초기화하시겠습니까?\n\n모든 로그 내용이 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write('')
                
                self.log_text.clear()
                self.info_label.setText("로그가 초기화되었습니다.")
                QMessageBox.information(self, "완료", "로그 파일이 초기화되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"로그 초기화 중 오류가 발생했습니다:\n{str(e)}")
    
    def closeEvent(self, event):
        """다이얼로그 닫을 때"""
        self.auto_refresh_timer.stop()
        event.accept()
