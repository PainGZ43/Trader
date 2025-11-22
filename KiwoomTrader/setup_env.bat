@echo off
chcp 65001 > nul
cls

echo.
echo ═══════════════════════════════════════════════════════
echo   키움 REST API 설정 도우미
echo ═══════════════════════════════════════════════════════
echo.

REM .env 파일 존재 확인
if exist .env (
    echo ✅ .env 파일이 이미 존재합니다.
    echo.
    choice /C YN /M "기존 파일을 백업하고 새로 만드시겠습니까? (Y/N)"
    if errorlevel 2 goto :END
    if errorlevel 1 (
        echo.
        echo 📦 기존 .env 파일 백업 중...
        copy /Y .env .env.backup
        echo ✅ 백업 완료: .env.backup
    )
)

echo.
echo ═══════════════════════════════════════════════════════
echo   📋 키움 API 정보 입력
echo ═══════════════════════════════════════════════════════
echo.
echo 💡 키움 개발자 포털에서 발급받은 정보를 입력하세요
echo    https://apiportal.kiwoom.com
echo.

REM APP_KEY 입력
:INPUT_APP_KEY
set /p APP_KEY="🔑 APP KEY를 입력하세요: "
if "%APP_KEY%"=="" (
    echo ❌ APP KEY를 입력해주세요!
    goto :INPUT_APP_KEY
)

echo.
REM SECRET_KEY 입력
:INPUT_SECRET_KEY
set /p SECRET_KEY="🔐 SECRET KEY를 입력하세요: "
if "%SECRET_KEY%"=="" (
    echo ❌ SECRET KEY를 입력해주세요!
    goto :INPUT_SECRET_KEY
)

echo.
REM 계좌번호 입력
:INPUT_ACCOUNT
set /p ACCOUNT_NO="💼 계좌번호 (8자리)를 입력하세요: "
if "%ACCOUNT_NO%"=="" (
    echo ❌ 계좌번호를 입력해주세요!
    goto :INPUT_ACCOUNT
)

echo.
echo ═══════════════════════════════════════════════════════
echo   ⚙️  시스템 설정
echo ═══════════════════════════════════════════════════════
echo.
echo 모드를 선택하세요:
echo   [1] SIMULATION (시뮬레이션 - 안전)
echo   [2] REAL (실전 - 실제 거래)
echo.
choice /C 12 /M "선택"

if errorlevel 2 (
    set MODE=REAL
    echo.
    echo ⚠️  실전 모드 선택됨! 주의하세요!
) else (
    set MODE=SIMULATION
    echo.
    echo ✅ 시뮬레이션 모드 선택됨
)

echo.
echo ═══════════════════════════════════════════════════════
echo   💾 .env 파일 생성 중...
echo ═══════════════════════════════════════════════════════

REM .env 파일 생성
(
echo # Kiwoom REST API Credentials
echo APP_KEY=%APP_KEY%
echo SECRET_KEY=%SECRET_KEY%
echo ACCOUNT_NO=%ACCOUNT_NO%
echo.
echo # KakaoTalk API Credentials
echo KAKAO_REST_API_KEY=your_kakao_rest_api_key
echo KAKAO_REDIRECT_URI=https://localhost:3000
echo KAKAO_ACCESS_TOKEN=your_access_token
echo KAKAO_REFRESH_TOKEN=your_refresh_token
echo.
echo # System Settings
echo MODE=%MODE%
echo LOG_LEVEL=INFO
) > .env

echo.
echo ✅ .env 파일 생성 완료!
echo.
echo ═══════════════════════════════════════════════════════
echo   📄 생성된 .env 파일 내용
echo ═══════════════════════════════════════════════════════
echo.
type .env
echo.

echo ═══════════════════════════════════════════════════════
echo   🧪 다음 단계
echo ═══════════════════════════════════════════════════════
echo.
echo 1. API 연결 테스트:
echo    python test_kiwoom.py
echo.
echo 2. 프로그램 실행:
echo    python main.py
echo.
echo 3. 문제 발생 시:
echo    - KIWOOM_REST_API_GUIDE.md 참고
echo    - .env 파일 내용 재확인
echo    - 키움 개발자 포털에서 API 승인 상태 확인
echo.

:END
echo.
pause
