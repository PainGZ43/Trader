@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════╗
echo ║   Premium Kiwoom AI Trader 실행        ║
echo ╚════════════════════════════════════════╝
echo.

REM Python 체크
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다!
    echo    Python 3.8-3.11을 설치해주세요.
    echo.
    echo    다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 감지됨
echo.

REM PyQt5 설치 여부 확인
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo 📦 필수 라이브러리 미설치 감지
    echo.
    echo ════════════════════════════════════════
    echo   자동 설치를 시작합니다...
    echo   시간이 좀 걸릴 수 있습니다 (3-5분)
    echo ════════════════════════════════════════
    echo.
    
    REM 기본 라이브러리 설치
    echo [1/3] 기본 UI 라이브러리 설치...
    pip install --quiet PyQt5 pyqtgraph qasync python-dotenv requests aiohttp
    
    echo [2/3] 데이터 분석 라이브러리 설치...
    pip install --quiet pandas numpy scikit-learn sqlalchemy beautifulsoup4 lxml joblib
    
    echo [3/3] AI 라이브러리 설치 (시간 소요)...
    pip install --quiet tensorflow xgboost yfinance 2>nul
    if errorlevel 1 (
        echo.
        echo ⚠️ AI 라이브러리 설치 실패 (선택사항)
        echo    기본 기능은 사용 가능합니다.
        echo.
    )
    
    echo.
    echo ✅ 라이브러리 설치 완료!
    echo.
    timeout /t 2 >nul
) else (
    echo ✅ 라이브러리 확인 완료
)

echo.
echo ════════════════════════════════════════
echo   프로그램을 시작합니다...
echo ════════════════════════════════════════
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ════════════════════════════════════════
    echo ❌ 오류가 발생했습니다!
    echo ════════════════════════════════════════
    echo.
    echo 로그 확인: logs/kiwoom_trader.log
    echo.
    echo 문제 해결:
    echo   1. Python 버전: python --version
    echo   2. 수동 설치: install.bat
    echo   3. 관리자 권한으로 실행
    echo.
    pause
)
