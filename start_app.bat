@echo off
echo ============================================================================
echo    AI STOCK PRICE PREDICTOR
echo ============================================================================
echo.

echo Starting application...
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start Flask application
python app.py

pause