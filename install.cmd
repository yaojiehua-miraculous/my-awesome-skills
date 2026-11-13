@echo off
rem ASCII-only launcher: all logic and messages live in scripts\install.ps1
rem (cmd.exe parses .cmd files with the OEM codepage, so Chinese here would break)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
echo.
pause
