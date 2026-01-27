@echo off
chcp 65001 > nul
title 앱 종료

echo ============================================
echo   🛑 메일머지 앱 종료
echo ============================================
echo.

:: Streamlit 프로세스 종료
echo 📌 실행 중인 Streamlit 프로세스를 종료합니다...

taskkill /f /im streamlit.exe > nul 2>&1
taskkill /f /fi "WINDOWTITLE eq streamlit*" > nul 2>&1

:: Python으로 실행 중인 streamlit 종료
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo list ^| find "PID"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | find "streamlit" >nul && taskkill /f /pid %%i >nul 2>&1
)

echo.
echo ✅ 종료 완료
echo.

timeout /t 2 > nul
