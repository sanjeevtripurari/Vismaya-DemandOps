@echo off
REM Windows batch script to run Vismaya DemandOps locally

echo ================================================
echo 🎯 Vismaya DemandOps - Local Runner (Windows)
echo Team MaximAI - AI-Powered FinOps Platform
echo ================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Virtual environment not found. Creating...
    python setup-venv.py
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation worked
if "%VIRTUAL_ENV%"=="" (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated: %VIRTUAL_ENV%

REM Install/update dependencies
echo 📦 Checking dependencies...
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt

REM Run the application
echo 🚀 Starting Vismaya DemandOps...
echo 📊 Dashboard will open at: http://localhost:8503
echo 🛑 Press Ctrl+C to stop the application
echo.

python start-vismaya.py

echo.
echo 👋 Application stopped
pause