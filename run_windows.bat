@echo off
setlocal
cd /d "%~dp0"
title Autonomous FinTech Team - Launcher

echo ================================================
echo   THE AUTONOMOUS FINTECH TEAM - TECHX 2026-2027
echo ================================================
echo.

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python was not found.
        echo Install Python 3.10 or newer from https://www.python.org/downloads/
        echo During installation, enable "Add python.exe to PATH".
        goto finish
    )
    set "PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    %PYTHON% -m venv .venv
    if errorlevel 1 goto error
) else (
    echo [1/4] Virtual environment already exists.
)

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 goto error

echo [3/4] Installing required packages...
python -m pip install --upgrade pip
if errorlevel 1 goto error
pip install -r requirements.txt
if errorlevel 1 goto error

echo [4/4] Starting the dashboard...
echo Keep this window open while using the website.
echo Open http://localhost:8501 in your browser.
echo.
streamlit run app.py
if errorlevel 1 goto error

goto finish

:error
echo.
echo The application could not start. Read the error shown above.
echo You can copy the error message and send it for troubleshooting.

:finish
echo.
echo Press any key to close this window.
pause >nul
endlocal
