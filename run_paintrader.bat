@echo off
echo Starting PainTrader...
call .venv\Scripts\activate
set PYTHONPATH=%CD%
python main.py
pause
