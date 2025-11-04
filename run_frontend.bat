@echo off
REM ====================================================================
REM Frontend Startup Script - Political Sentiment Alpha Platform
REM ====================================================================

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Political Sentiment Alpha Platform - Frontend                 ║
echo ║    React Development Server                                       ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

cd frontend

REM Check if Node.js is installed
where node >nul 2>nul
if errorlevel 1 (
    echo [X] Node.js is not installed!
    echo [!] Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [√] Node.js found: 
node --version

REM Check if node_modules exists
if not exist "node_modules" (
    echo [!] Dependencies not installed. Installing...
    npm install
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [√] Dependencies installed
) else (
    echo [√] Dependencies already installed
)

REM Start React development server
echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Starting React Development Server                              ║
echo ║    URL: http://localhost:3000                                     ║
echo ║    Press Ctrl+C to stop                                           ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

npm start

pause

