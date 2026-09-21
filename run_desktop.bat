@echo off
title Mobile Store Desktop POS
echo Starting Mobile Store Desktop Application...
cd /d "%~dp0"
python desktop\main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred running desktop app.
    pause
)
