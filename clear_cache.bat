@echo off
chcp 65001 > nul
title 캐시 정리

echo ============================================
echo   🧹 캐시 및 임시 파일 정리
echo ============================================
echo.

:: Streamlit 캐시 삭제
echo 📌 Streamlit 캐시 삭제 중...
if exist "%USERPROFILE%\.streamlit\cache" (
    rmdir /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
    echo ✅ Streamlit 캐시 삭제 완료
) else (
    echo    캐시 폴더가 없습니다.
)

:: __pycache__ 삭제
echo.
echo 📌 Python 캐시 삭제 중...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)
echo ✅ Python 캐시 삭제 완료

:: .pyc 파일 삭제
echo.
echo 📌 .pyc 파일 삭제 중...
del /s /q *.pyc 2>nul
echo ✅ .pyc 파일 삭제 완료

echo.
echo ============================================
echo   ✅ 캐시 정리 완료!
echo ============================================
echo.

pause
