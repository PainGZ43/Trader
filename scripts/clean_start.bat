@echo off
echo [INFO] Killing all running Python processes to ensure clean state...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM PainTrader.exe /T >nul 2>&1

echo [INFO] Clearing logs...
del /Q logs\*.log >nul 2>&1

echo [INFO] Starting PainTrader...
python main.py
pause
