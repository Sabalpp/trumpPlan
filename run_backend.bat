@echo off
REM ====================================================================
REM Backend Startup Script - Political Sentiment Alpha Platform
REM ====================================================================

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Political Sentiment Alpha Platform - Backend API              ║
echo ║    Flask REST API Server                                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo [!] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [√] Virtual environment created
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo [X] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [*] Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [!] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [√] Dependencies installed
) else (
    echo [√] Dependencies already installed
)

REM Start Flask server
echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Starting Flask API Server                                      ║
echo ║    URL: http://localhost:5000                                     ║
echo ║    Press Ctrl+C to stop                                           ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

python app/main.py

pause

