@echo off
chcp 65001 > nul
title 메일머지 시스템 - 설치 및 실행

echo ============================================
echo   📧 지능형 그룹핑 메일머지 시스템
echo   원클릭 설치 및 실행
echo ============================================
echo.

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo.
    echo    1. https://www.python.org/downloads/ 에서 Python 3.8+ 설치
    echo    2. 설치 시 "Add Python to PATH" 체크 필수!
    echo    3. 설치 후 이 파일을 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

echo ✅ Python 확인 완료
echo.

:: 가상환경 확인 및 생성
if not exist "venv" (
    echo 📌 가상환경 생성 중...
    python -m venv venv
    echo ✅ 가상환경 생성 완료
    echo.
)

:: 가상환경 활성화
echo 📌 가상환경 활성화...
call venv\Scripts\activate.bat

:: pip 업그레이드 및 종속성 설치
echo 📌 패키지 설치 중... (최초 실행 시 몇 분 소요)
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo.
echo ============================================
echo   🚀 앱 시작!
echo ============================================
echo.
echo    브라우저에서 http://localhost:8501 이 자동으로 열립니다.
echo    종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.

streamlit run app.py

pause
