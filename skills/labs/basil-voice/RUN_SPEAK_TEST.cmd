@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" ( echo Run RUN_SETUP.cmd first. & pause & exit /b 2 )
".venv\Scripts\python.exe" basil_voice.py speak "Right. The evidence is quite clear. We are going to do the useful thing first and admire the paperwork afterwards." --output output\basil_first_test.wav
echo.
echo Output: output\basil_first_test.wav
pause
