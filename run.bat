@echo off
title PainTrader AI - Pro
echo ==================================================
echo       Starting PainTrader AI System...
echo ==================================================

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
