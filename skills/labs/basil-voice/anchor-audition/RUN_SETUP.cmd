@echo off
setlocal
cd /d "%~dp0"
echo.
echo BASIL BRITISH ANCHOR AUDITION v0.1 - SETUP
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path '.\SETUP_WINDOWS.ps1'),[ref]$null,[ref]$e) ^| Out-Null; if($e.Count){$e ^| %% {Write-Host $_ -ForegroundColor Red}; exit 9} else {Write-Host 'Parser check passed.' -ForegroundColor Green}"
if errorlevel 1 (
  echo.
  echo PowerShell parser check failed.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_WINDOWS.ps1"
set CODE=%ERRORLEVEL%
echo.
if not "%CODE%"=="0" echo Setup stopped with exit code %CODE%.
pause
exit /b %CODE%
