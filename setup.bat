@echo off
echo ============================================================================
echo    AI STOCK PRICE PREDICTOR - SETUP SCRIPT
echo ============================================================================
echo.

echo [1/4] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

echo [2/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

echo [4/4] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] All dependencies installed successfully
echo.

echo ============================================================================
echo    SETUP COMPLETE!
echo ============================================================================
echo.
echo To start the application:
echo   1. Run: start_app.bat
echo   2. Open browser: http://localhost:5000
echo.
echo Press any key to exit...
pause >nul