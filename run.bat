@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║        🚀 Upbit Auto Trader - 자동 실행 스크립트        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM 관리자 권한 확인 (선택사항)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [경고] 관리자 권한이 없습니다. 일부 기능이 제한될 수 있습니다.
    echo.
)

REM Python 설치 확인
echo [1/6] Python 설치 확인 중...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 3.9 이상을 설치해주세요: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 감지됨
echo.

REM 가상환경 확인 및 생성
echo [2/6] 가상환경 확인 중...
if not exist "venv\" (
    echo 가상환경이 없습니다. 새로 생성합니다...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo [오류] 가상환경 생성 실패!
        pause
        exit /b 1
    )
    echo ✅ 가상환경 생성 완료
) else (
    echo ✅ 가상환경이 이미 존재합니다
)
echo.

REM 가상환경 활성화
echo [3/6] 가상환경 활성화 중...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [오류] 가상환경 활성화 실패!
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화 완료
echo.

REM pip 업그레이드
echo [4/6] pip 업그레이드 중...
python -m pip install --upgrade pip --quiet
if %errorLevel% neq 0 (
    echo [경고] pip 업그레이드 실패. 계속 진행합니다...
) else (
    echo ✅ pip 업그레이드 완료
)
echo.

REM 의존성 패키지 설치
echo [5/6] 필수 패키지 설치 중...
echo (이 작업은 처음 실행 시 시간이 걸릴 수 있습니다)
echo.

REM requirements.txt 확인
if not exist "requirements.txt" (
    echo [오류] requirements.txt 파일을 찾을 수 없습니다!
    pause
    exit /b 1
)

REM 패키지 설치
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorLevel% neq 0 (
    echo [경고] 일부 패키지 설치 실패. 세부 설치를 진행합니다...
    echo.
    pip install -r requirements.txt
)

REM pyupbit 설치 확인 (requirements.txt에 누락된 경우)
python -c "import pyupbit" >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [추가] pyupbit 패키지 설치 중...
    pip install pyupbit --quiet
    if %errorLevel% neq 0 (
        echo [오류] pyupbit 설치 실패!
        pause
        exit /b 1
    )
    echo ✅ pyupbit 설치 완료
)

echo.
echo ✅ 모든 패키지 설치 완료
echo.

REM 필요한 디렉토리 생성
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "models" mkdir models

REM 프로그램 실행
echo [6/6] 프로그램 실행 중...
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║              프로그램을 시작합니다...                   ║
echo ║          종료하려면 창을 닫거나 Ctrl+C를 누르세요        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM main.py 확인
if not exist "main.py" (
    echo [오류] main.py 파일을 찾을 수 없습니다!
    echo.
    pause
    exit /b 1
)

REM 프로그램 실행 (에러 발생 시 대기)
python main.py
set EXIT_CODE=%errorLevel%

echo.
echo ════════════════════════════════════════════════════════
if %EXIT_CODE% equ 0 (
    echo 프로그램이 정상적으로 종료되었습니다.
) else (
    echo [오류] 프로그램이 오류와 함께 종료되었습니다. (코드: %EXIT_CODE%)
    echo.
    echo 문제 해결 방법:
    echo 1. 로그 파일을 확인하세요 (logs 폴더)
    echo 2. Python 버전이 3.9 이상인지 확인하세요
    echo 3. 모든 패키지가 올바르게 설치되었는지 확인하세요
    echo 4. .env 파일에 API 키가 올바르게 설정되었는지 확인하세요
)
echo ════════════════════════════════════════════════════════
echo.
pause
