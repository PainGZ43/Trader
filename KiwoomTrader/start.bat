@echo off
chcp 65001 >nul
cls

:menu
echo ╔════════════════════════════════════════╗
echo ║   Premium Kiwoom AI Trader             ║
echo ║   간편 실행 메뉴                       ║
echo ╚════════════════════════════════════════╝
echo.
echo [1] 프로그램 실행
echo [2] AI 모델 학습
echo [3] 라이브러리 설치
echo [4] 백테스트만 실행
echo [5] 종료
echo.
set /p choice=선택하세요 (1-5): 

if "%choice%"=="1" goto run
if "%choice%"=="2" goto train
if "%choice%"=="3" goto install
if "%choice%"=="4" goto backtest
if "%choice%"=="5" goto end

echo 잘못된 입력입니다.
pause
cls
goto menu

:run
cls
echo ▶ 프로그램 실행 중...
echo.
python main.py
pause
cls
goto menu

:train
cls
echo ▶ AI 모델 학습 중...
echo.
echo 종목 코드를 입력하세요 (기본: 005930):
set /p code=
if "%code%"=="" set code=005930

echo.
echo 학습 기간 (6mo/1y/2y/5y, 기본: 1y):
set /p period=
if "%period%"=="" set period=1y

echo.
echo 데이터 간격 (1h/1d, 기본: 1h):
set /p interval=
if "%interval%"=="" set interval=1h

echo.
echo 학습 시작: %code% %period% %interval%
echo 약 10-15분 소요됩니다...
echo.
python train_ai.py %code% %period% %interval%
pause
cls
goto menu

:install
cls
echo ▶ 라이브러리 설치 중...
echo.
pip install -r requirements.txt
echo.
echo ✅ 설치 완료!
pause
cls
goto menu

:backtest
cls
echo ▶ 백테스트 실행
echo.
echo (UI를 통해 백테스트를 실행하세요)
python main.py
pause
cls
goto menu

:end
echo.
echo 종료합니다.
exit /b 0
