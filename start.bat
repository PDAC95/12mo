@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                     12mo Budget Tracker - Development Server                 ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔍 Checking environment...

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo ⚠️  Virtual environment not detected. Activating...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        echo ✅ Virtual environment activated!
    ) else (
        echo ❌ Virtual environment not found! Please run: python -m venv venv
        pause
        exit /b 1
    )
) else (
    echo ✅ Virtual environment is active: %VIRTUAL_ENV%
)

echo.
echo 🔧 Installing/updating dependencies...
pip install -q -r requirements.txt

echo.
echo 🗄️  Running database migrations...
python manage.py migrate --verbosity=0

echo.
echo 🎯 Starting enhanced development server...
echo.

REM Start the enhanced server
python start_dev.py

pause