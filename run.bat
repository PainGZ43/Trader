@echo off
title PainTrader AI - Pro
echo ==================================================
echo       Starting PainTrader AI System...
echo ==================================================

:: --- Clean Start Logic ---
echo [INFO] Performing Clean Start...
echo [INFO] Killing all running Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM PainTrader.exe /T >nul 2>&1

echo [INFO] Clearing logs...
if exist "logs" (
    del /Q logs\*.log >nul 2>&1
)
:: -------------------------

:: Activate Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

:: Set PYTHONPATH to current directory
set PYTHONPATH=%~dp0

:: Run Main Application
python main.py

:: Pause if error occurs
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application crashed with exit code %ERRORLEVEL%
    pause
)
