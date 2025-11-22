@echo off
chcp 65001 >nul
echo ================================
echo 라이브러리 설치 중...
echo ================================
echo.
echo [1/2] 기본 라이브러리 설치...
pip install --only-binary :all: PyQt5 pyqtgraph requests aiohttp numpy scikit-learn sqlalchemy beautifulsoup4 lxml joblib pyinstaller

echo.
echo [2/2] pandas 및 AI 라이브러리 설치...
pip install pandas --only-binary :all:
pip install tensorflow --only-binary :all:
pip install xgboost yfinance

echo.
echo ================================
echo 설치 완료!
echo ================================
echo.
echo 만약 오류가 발생했다면:
echo 1. Python 버전 확인: python --version
echo 2. Python은 3.8-3.11 사용 권장
echo 3. 32bit Python은 일부 라이브러리 지원 안됨
echo.
pause
