@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" ( echo Run RUN_SETUP.cmd first. & pause & exit /b 2 )
".venv\Scripts\python.exe" basil_voice.py serve --host 127.0.0.1 --port 8765
pause
