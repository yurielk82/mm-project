@echo off
chcp 65001 > nul
title SMTP 설정 파일 생성

echo ============================================
echo   ⚙️ SMTP 설정 파일 생성
echo ============================================
echo.

:: .streamlit 폴더 생성
if not exist ".streamlit" (
    mkdir .streamlit
    echo ✅ .streamlit 폴더 생성 완료
)

:: secrets.toml 파일 존재 확인
if exist ".streamlit\secrets.toml" (
    echo.
    echo ⚠️  secrets.toml 파일이 이미 존재합니다.
    echo    덮어쓰시겠습니까?
    echo.
    set /p overwrite="덮어쓰기 (Y/N): "
    if /i not "%overwrite%"=="Y" (
        echo 취소되었습니다.
        pause
        exit /b 0
    )
)

echo.
echo 📌 SMTP 정보를 입력하세요.
echo    (하이웍스 예: smtp.hiworks.com / 465)
echo.

set /p smtp_server="SMTP 서버 주소: "
set /p smtp_port="SMTP 포트 (465 또는 587): "
set /p smtp_id="이메일 주소: "
set /p smtp_pw="비밀번호 (앱 비밀번호 권장): "
set /p sender_name="발신자 이름: "

echo.
echo 📌 secrets.toml 파일 생성 중...

(
echo # SMTP 설정
echo SMTP_SERVER = "%smtp_server%"
echo SMTP_PORT = %smtp_port%
echo SMTP_ID = "%smtp_id%"
echo SMTP_PW = "%smtp_pw%"
echo SENDER_NAME = "%sender_name%"
echo SMTP_PROVIDER = "custom"
) > .streamlit\secrets.toml

echo.
echo ============================================
echo   ✅ 설정 완료!
echo ============================================
echo.
echo    설정 파일: .streamlit\secrets.toml
echo.
echo    ⚠️  주의: 이 파일은 절대 GitHub에 업로드하지 마세요!
echo.

pause
