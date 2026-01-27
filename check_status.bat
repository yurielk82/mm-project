@echo off
chcp 65001 > nul
title 시스템 상태 확인

echo ============================================
echo   🔍 시스템 상태 확인
echo ============================================
echo.

:: Python 버전
echo [Python]
python --version 2>nul || echo ❌ Python이 설치되어 있지 않습니다.
echo.

:: pip 버전
echo [pip]
pip --version 2>nul || echo ❌ pip를 찾을 수 없습니다.
echo.

:: Streamlit 버전
echo [Streamlit]
pip show streamlit 2>nul | findstr "Version" || echo ❌ Streamlit이 설치되어 있지 않습니다.
echo.

:: 가상환경 확인
echo [가상환경]
if exist "venv" (
    echo ✅ venv 폴더 존재
) else (
    echo ⚠️  가상환경이 생성되지 않았습니다. setup_and_run.bat을 실행하세요.
)
echo.

:: secrets.toml 확인
echo [SMTP 설정]
if exist ".streamlit\secrets.toml" (
    echo ✅ secrets.toml 파일 존재
) else (
    echo ⚠️  SMTP 설정 파일이 없습니다. create_secrets.bat을 실행하세요.
)
echo.

:: 필수 패키지 확인
echo [필수 패키지]
pip show pandas >nul 2>&1 && echo ✅ pandas || echo ❌ pandas
pip show openpyxl >nul 2>&1 && echo ✅ openpyxl || echo ❌ openpyxl
pip show extra-streamlit-components >nul 2>&1 && echo ✅ extra-streamlit-components || echo ❌ extra-streamlit-components
pip show plotly >nul 2>&1 && echo ✅ plotly || echo ❌ plotly
echo.

:: 실행 중인 앱 확인
echo [앱 실행 상태]
netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  앱이 실행 중이지 않습니다.
) else (
    echo ✅ 포트 8501에서 앱이 실행 중입니다.
    echo    http://localhost:8501
)
echo.

echo ============================================
pause
