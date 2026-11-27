@echo off
title WinDebloatX Launcher
cd /d "%~dp0"

:: Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Administrator privileges required. Requesting UAC elevation...
    powershell -Command "Start-Process python -ArgumentList 'main.py' -Verb RunAs"
    exit /b
)

python main.py %*
pause
