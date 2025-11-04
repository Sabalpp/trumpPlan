@echo off
REM ====================================================================
REM Full Stack Startup Script - Political Sentiment Alpha Platform
REM ====================================================================

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Political Sentiment Alpha Platform                            ║
echo ║    Starting Backend + Frontend                                    ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Start backend in new window
echo [*] Starting Backend API Server...
start "Backend API - Port 5000" cmd /k "run_backend.bat"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo [*] Starting Frontend Dev Server...
start "Frontend React - Port 3000" cmd /k "run_frontend.bat"

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    Both servers starting in separate windows                      ║
echo ║                                                                    ║
echo ║    Backend:  http://localhost:5000                                ║
echo ║    Frontend: http://localhost:3000                                ║
echo ║                                                                    ║
echo ║    Close those windows to stop the servers                        ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

pause

