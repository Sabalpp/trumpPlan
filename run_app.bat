@echo off
echo ========================================
echo Political Sentiment Alpha Platform
echo Starting Setup and Server...
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Install from python.org
    pause
    exit /b 1
)

echo.
echo [2/6] Creating virtual environment...
if not exist venv (
    python -m venv venv
)

echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/6] Installing requirements...
pip install flask flask-cors sqlalchemy python-dotenv pandas numpy vaderSentiment yfinance scipy statsmodels

echo.
echo [5/6] Creating .env file...
if not exist .env (
    (
        echo ALPHA_VANTAGE_API_KEY=DEMO_KEY
        echo SECRET_KEY=my-secret-key-12345
        echo DATABASE_URL=sqlite:///political_alpha.db
        echo FLASK_ENV=development
    ) > .env
    echo Created .env file
) else (
    echo .env file already exists
)

echo.
echo [6/6] Initializing database...
python -c "from models.db import init_db; init_db()" 2>nul
if errorlevel 1 (
    echo Database initialization skipped or already done
)

echo.
echo ========================================
echo Starting Flask Server...
echo ========================================
echo.
echo Server will start at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app\main.py

pause

