@echo off
echo =====================================================
echo   Khmer Dubbing Studio - Setup
echo =====================================================
echo.

REM Check Python 3.11
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from https://python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment with Python 3.11...
py -3.11 -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo =====================================================
echo   Setup Complete!
echo =====================================================
echo.
echo To run the application:
echo   1. Double-click run.bat
echo   OR
echo   1. Open terminal in this folder
echo   2. Run: venv\Scripts\activate
echo   3. Run: python main.py
echo.
pause
