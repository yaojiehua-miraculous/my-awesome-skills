@echo off
rem ASCII-only launcher: all logic and messages live in scripts\uninstall.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall.ps1"
echo.
pause
