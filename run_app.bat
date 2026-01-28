@echo off
chcp 65001 > nul 2>&1
title CSO Mail Merge System

echo ============================================
echo   CSO Mail Merge System
echo ============================================
echo.

:: Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo         Please install from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Check if streamlit is installed
python -c "import streamlit" > nul 2>&1
if errorlevel 1 (
    echo [WARN] Dependencies not installed.
    echo [INFO] Installing dependencies...
    echo.
    pip install -r requirements.txt
    echo.
)

:: Check streamlit again after install
python -c "import streamlit" > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo         Please run 'install_dependencies.bat' first.
    pause
    exit /b 1
)

echo [OK] Dependencies ready
echo [INFO] Starting application...
echo.
echo    Browser will open at http://localhost:8501
echo    Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
