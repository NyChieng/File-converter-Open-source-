@echo off
title FileConverter
cd /d "%~dp0"

echo ============================================
echo   FileConverter - Starting Up
echo ============================================
echo.

:: Check Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if missing
if not exist "venv\" (
    echo Creating virtual environment...
    py -m venv venv
)

:: Activate
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -q -r backend\requirements.txt

:: Start server
echo.
echo Starting server at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
start "" http://127.0.0.1:8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
