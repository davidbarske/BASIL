@echo off
setlocal
cd /d "%~dp0"

echo.
echo BASIL BRITISH ANCHOR AUDITION v0.3 - SETUP
echo.
echo [PRELAUNCH] Checking PowerShell setup script...

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0PRECHECK_POWERSHELL.ps1"
set "PRECHECK_CODE=%ERRORLEVEL%"

if not "%PRECHECK_CODE%"=="0" (
  echo.
  echo PowerShell parser check failed.
  pause
  exit /b %PRECHECK_CODE%
)

echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_WINDOWS.ps1"
set "CODE=%ERRORLEVEL%"

echo.
if "%CODE%"=="0" (
  echo Setup completed successfully.
) else (
  echo Setup stopped with exit code %CODE%.
)
echo.
pause
exit /b %CODE%
