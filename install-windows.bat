@echo off
rem Double-click or run from cmd to install PiperScribe on Windows.
rem Passes any arguments (for example -Dev) through to install-windows.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1" %*
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (echo Install finished.) else (echo Install failed with exit code %RESULT%.)
pause
exit /b %RESULT%
