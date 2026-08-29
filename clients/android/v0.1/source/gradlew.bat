@echo off
where gradle >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  gradle %*
  exit /b %ERRORLEVEL%
)
echo Gradle is not installed on PATH. Open the project in Android Studio, or install Gradle 8.9.
exit /b 1
