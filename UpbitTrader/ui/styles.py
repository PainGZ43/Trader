"""
UI 스타일 정의 - 업비트 스타일 다크 테마
"""

# 다크 모드 색상
COLORS_DARK = {
    'background_main': '#1e2329',
    'background_secondary': '#2b3139',
    'background_tertiary': '#181a20',
    'text_primary': '#ffffff',
    'text_secondary': '#b7bdc6',
    'text_disabled': '#5e6673',
    'primary': '#fcd535',
    'success': '#0ecb81',
    'danger': '#f6465d',
    'info': '#1fc7d4',
    'warning': '#f0b90b',
    'chart_up': '#14b079',
    'chart_down': '#f6465d',
    'border': '#2b3139',
}

# 다크 테마 스타일시트
DARK_STYLESHEET = f"""
    /* 전역 스타일 */
    QWidget {{
        background-color: {COLORS_DARK['background_main']};
        color: {COLORS_DARK['text_primary']};
        font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
        font-size: 13px;
    }}
    
    /* 메인 윈도우 */
    QMainWindow {{
        background-color: {COLORS_DARK['background_main']};
    }}
    
    /* 스플리터 */
    QSplitter::handle {{
        background-color: {COLORS_DARK['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    
    /* 버튼 */
    QPushButton {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_primary']};
        border: 1px solid {COLORS_DARK['border']};
        border-radius: 4px;
        padding: 8px 16px;
        min-height: 32px;
    }}
    QPushButton:hover {{
        background-color: #3a3f47;
        border-color: {COLORS_DARK['primary']};
    }}
    QPushButton:pressed {{
        background-color: #2b3139;
    }}
    QPushButton:disabled {{
        background-color: #2b3139;
        color: {COLORS_DARK['text_disabled']};
    }}
    
    /* 매수 버튼 */
    QPushButton[buttonType="buy"] {{
        background-color: {COLORS_DARK['success']};
        color: white;
        border: none;
        font-weight: bold;
    }}
    QPushButton[buttonType="buy"]:hover {{
        background-color: #10d98f;
    }}
    
    /* 매도 버튼 */
    QPushButton[buttonType="sell"] {{
        background-color: {COLORS_DARK['danger']};
        color: white;
        border: none;
        font-weight: bold;
    }}
    QPushButton[buttonType="sell"]:hover {{
        background-color: #ff526f;
    }}
    
    /* 라인 에디트 (입력창) */
    QLineEdit {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_primary']};
        border: 1px solid {COLORS_DARK['border']};
        border-radius: 4px;
        padding: 8px;
        min-height: 32px;
    }}
    QLineEdit:focus {{
        border-color: {COLORS_DARK['primary']};
    }}
    
    /* 테이블 */
    QTableWidget {{
        background-color: {COLORS_DARK['background_main']};
        alternate-background-color: {COLORS_DARK['background_secondary']};
        gridline-color: {COLORS_DARK['border']};
        border: none;
    }}
    QTableWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {COLORS_DARK['border']};
    }}
    QTableWidget::item:selected {{
        background-color: {COLORS_DARK['background_secondary']};
    }}
    QHeaderView::section {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_secondary']};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {COLORS_DARK['border']};
        font-weight: bold;
    }}
    
    /* 탭 위젯 */
    QTabWidget::pane {{
        border: 1px solid {COLORS_DARK['border']};
        background-color: {COLORS_DARK['background_main']};
    }}
    QTabBar::tab {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_secondary']};
        padding: 10px 20px;
        border: none;
        border-right: 1px solid {COLORS_DARK['border']};
    }}
    QTabBar::tab:selected {{
        background-color: {COLORS_DARK['background_main']};
        color: {COLORS_DARK['primary']};
        font-weight: bold;
    }}
    QTabBar::tab:hover {{
        background-color: #3a3f47;
    }}
    
    /* 스크롤바 */
    QScrollBar:vertical {{
        background-color: {COLORS_DARK['background_main']};
        width: 12px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS_DARK['background_secondary']};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: #3a3f47;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* 라벨 */
    QLabel {{
        background-color: transparent;
        color: {COLORS_DARK['text_primary']};
    }}
    
    /* 콤보박스 */
    QComboBox {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_primary']};
        border: 1px solid {COLORS_DARK['border']};
        border-radius: 4px;
        padding: 6px;
        min-height: 32px;
    }}
    QComboBox:hover {{
        border-color: {COLORS_DARK['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS_DARK['background_secondary']};
        color: {COLORS_DARK['text_primary']};
        selection-background-color: #3a3f47;
    }}
"""
