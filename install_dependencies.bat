@echo off
chcp 65001 > nul
title 종속성 설치

echo ============================================
echo   📦 종속성 패키지 설치
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
echo.

:: pip 업그레이드
echo 📌 pip 업그레이드 중...
python -m pip install --upgrade pip

echo.
echo 📌 종속성 패키지 설치 중...
echo.

pip install -r requirements.txt

echo.
if errorlevel 1 (
    echo ❌ 설치 중 오류가 발생했습니다.
) else (
    echo ============================================
    echo   ✅ 설치 완료!
    echo ============================================
    echo.
    echo   이제 run_app.bat을 실행하여 앱을 시작하세요.
)

echo.
pause
