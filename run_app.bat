@echo off
chcp 65001 > nul
title 메일머지 시스템 실행

echo ============================================
echo   📧 지능형 그룹핑 메일머지 시스템
echo ============================================
echo.

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo    https://www.python.org/downloads/ 에서 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Python 확인 완료
echo 🚀 앱을 시작합니다...
echo.
echo    브라우저에서 http://localhost:8501 이 자동으로 열립니다.
echo    종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.

streamlit run app.py

pause
