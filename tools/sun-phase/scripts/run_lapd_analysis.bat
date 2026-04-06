@echo off
REM LAPD Crime Data Phase Analysis
REM This script processes LAPD crime data to determine if streetlights were ON

echo ============================================================
echo LAPD Crime Data - Streetlight Phase Analysis
echo ============================================================

REM Navigate to repo root
cd /d "%~dp0.."

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found.
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if input file is provided
if "%1"=="" (
    echo.
    echo Usage: run_lapd_analysis.bat [input_csv_filename]
    echo.
    echo Example: run_lapd_analysis.bat "Crime_Data_from_2010_to_2019.csv"
    echo.
    echo The input file should be in the data/input folder.
    echo Output will be saved to the data/output folder.
    pause
    exit /b 1
)

set INPUT_FILE=data\input\%1
set OUTPUT_FILE=data\output\%~n1_with_phase.csv

echo.
echo Input:  %INPUT_FILE%
echo Output: %OUTPUT_FILE%
echo.

venv\Scripts\python phase_calculator.py "%INPUT_FILE%" "%OUTPUT_FILE%" --lat LAT --lon LON --date "DATE OCC" --time "TIME OCC"

echo.
echo ============================================================
echo Analysis complete!
echo ============================================================
pause
