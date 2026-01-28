@echo off
chcp 65001 > nul 2>&1
title Mail Merge System

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
echo [INFO] Starting application...
echo.
echo    Browser will open at http://localhost:8501
echo    Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
