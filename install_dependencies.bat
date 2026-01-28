@echo off
chcp 65001 > nul 2>&1
title Install Dependencies

echo ============================================
echo   Install Dependencies
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

:: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Installing dependencies...
echo.

pip install -r requirements.txt

echo.
if errorlevel 1 (
    echo [ERROR] Installation failed.
) else (
    echo ============================================
    echo   [SUCCESS] Installation Complete!
    echo ============================================
    echo.
    echo   Run 'run_app.bat' to start the application.
)

echo.
pause
