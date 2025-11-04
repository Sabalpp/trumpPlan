@echo off
echo ========================================
echo Installing Political Sentiment Alpha Platform
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not installed!
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo.
echo [2/5] Creating virtual environment...
python -m venv venv

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/5] Installing all requirements...
echo This may take 3-5 minutes...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [5/5] Downloading NLP model...
python -m spacy download en_core_web_sm

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create .env file with your API keys
echo 2. Run: run_app.bat
echo.
pause

