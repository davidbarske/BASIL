@echo off
setlocal
cd /d "%~dp0"
set "PS1=%~dp0SETUP_WINDOWS.ps1"
set "LOG=%~dp0SETUP_DIAGNOSTICS.txt"

echo BASIL VOICE CAPABILITY v0.3 - SETUP
echo.
echo [PRELAUNCH] Checking PowerShell setup script...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile($env:PS1,[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e | ForEach-Object { Write-Host ('Line '+$_.Extent.StartLineNumber+': '+$_.Message) -ForegroundColor Red };exit 91}else{Write-Host 'Parser check passed.' -ForegroundColor Green;exit 0}"
if errorlevel 1 (
  echo.
  echo SAFETY STOP: setup script was not executed.
  pause
  exit /b 91
)

echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "& '%PS1%' *>&1 | Tee-Object -FilePath '%LOG%'; exit $LASTEXITCODE"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Setup stopped with exit code %RC%.
  echo Diagnostics: %LOG%
) else (
  echo Setup completed successfully.
)
echo.
pause
exit /b %RC%
