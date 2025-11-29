@echo off
echo Running PainTrader Tests...
call .venv\Scripts\activate
set PYTHONPATH=%CD%
python -m unittest discover tests
pause
