@echo off
REM Quick CLI Test for Financial Rules Extraction Agent
REM Run this script to test the CLI with the Saudi law document

echo.
echo ========================================
echo Financial Rules Extraction - CLI Test
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo WARNING: Virtual environment not detected
    echo Please activate your venv first:
    echo   .venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Virtual Environment: %VIRTUAL_ENV%
echo.

REM Test 1: List tracks
echo [1/3] Listing available tracks...
echo ----------------------------------------
python cli.py list-tracks
if errorlevel 1 (
    echo ERROR: Failed to list tracks
    pause
    exit /b 1
)
echo.

REM Test 2: Extract rules (fast mode)
echo [2/3] Extracting rules from Saudi Civil Service Law...
echo URL: https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/fd30f9c7-8606-4367-bb22-a9a700f2d952/1
echo ----------------------------------------
python cli.py extract --name "Saudi Civil Service Law" --url "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/fd30f9c7-8606-4367-bb22-a9a700f2d952/1"
if errorlevel 1 (
    echo ERROR: Extraction failed
    pause
    exit /b 1
)
echo.

REM Test 3: Show output
echo [3/3] Checking output files...
echo ----------------------------------------
dir /B /O:-D output\extraction_*.json 2>nul | findstr "extraction_" >nul
if errorlevel 1 (
    echo WARNING: No output files found
) else (
    echo Latest extraction results:
    dir /B /O:-D output\extraction_*.json | head -n 1
    echo.
    echo Full output directory:
    dir /B output\extraction_*.json 2>nul
)
echo.

echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Check the 'output' folder for JSON results
echo.

pause
