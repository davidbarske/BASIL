@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run RUN_SETUP.cmd first.
  pause
  exit /b 2
)
set "ESPEAK=C:\Program Files\eSpeak NG"
if exist "%ESPEAK%\espeak-ng.exe" set "PATH=%ESPEAK%;%PATH%"
echo.
echo BASIL BRITISH ANCHOR AUDITION v0.1
echo Generating seven British male anchors. This should be far faster than Qwen VoiceDesign.
echo.
".venv\Scripts\python.exe" "anchor_audition.py" generate
set CODE=%ERRORLEVEL%
echo.
if "%CODE%"=="0" (
  echo Complete. Open the output folder and listen to the seven numbered WAV files.
) else (
  echo Audition stopped with exit code %CODE%.
)
echo.
pause
exit /b %CODE%
