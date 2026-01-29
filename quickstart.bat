@echo off
REM Quick start script for Windows
REM Financial Rules Extraction Agent

echo ========================================
echo Financial Rules Extraction Agent
echo Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please edit .env file and add your AIXPLAIN_API_KEY
    echo.
    pause
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Choose an option:
echo   1. Run Web Interface (Streamlit)
echo   2. Run Example Script
echo   3. Run CLI Help
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Starting Streamlit web interface...
    streamlit run app.py
) else if "%choice%"=="2" (
    echo.
    echo Running example script...
    python examples\example.py
    pause
) else if "%choice%"=="3" (
    echo.
    python cli.py --help
    echo.
    pause
) else (
    echo.
    echo Goodbye!
)

deactivate
