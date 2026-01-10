@echo off
chcp 65001 > nul
title 호요봇 설정 마법사

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║            🎮 호요봇 초기 설정 마법사 🎮                   ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 이 마법사는 봇 실행에 필요한 설정 파일을 자동으로 생성합니다.
echo.
echo ─────────────────────────────────────────────────────────────
echo.

REM .env 파일이 이미 있는지 확인
if exist ".env" (
    echo ⚠️  .env 파일이 이미 존재합니다!
    echo.
    set /p overwrite="덮어쓰시겠습니까? (Y/N): "
    if /i not "%overwrite%"=="Y" (
        echo.
        echo ❌ 설정이 취소되었습니다.
        pause
        exit /b
    )
    echo.
)

echo ─────────────────────────────────────────────────────────────
echo.
echo 📋 디스코드 봇 토큰 입력
echo.
echo    토큰을 얻는 방법:
echo    1. https://discord.com/developers 접속
echo    2. New Application 클릭 → 앱 생성
echo    3. 왼쪽 메뉴에서 Bot 클릭
echo    4. Reset Token 클릭 → 토큰 복사
echo.
echo ─────────────────────────────────────────────────────────────
echo.

set /p discord_token="디스코드 봇 토큰을 붙여넣으세요: "

if "%discord_token%"=="" (
    echo.
    echo ❌ 토큰이 입력되지 않았습니다!
    pause
    exit /b
)

echo.
echo ─────────────────────────────────────────────────────────────
echo.
echo 📋 Gemini API 키 입력 (선택사항 - AI 채팅 기능용)
echo.
echo    API 키를 얻는 방법:
echo    1. https://aistudio.google.com 접속
echo    2. API Keys 메뉴에서 키 생성
echo.
echo    (사용하지 않으려면 그냥 Enter를 누르세요)
echo.
echo ─────────────────────────────────────────────────────────────
echo.

set /p gemini_key="Gemini API 키 (선택사항): "

echo.
echo ─────────────────────────────────────────────────────────────
echo.
echo 📝 설정 파일 생성 중...
echo.

REM .env 파일 생성
(
echo DISCORD_TOKEN="%discord_token%"
if not "%gemini_key%"=="" echo GEMINI_API_KEY="%gemini_key%"
) > .env

echo ✅ .env 파일이 생성되었습니다!
echo.
echo ─────────────────────────────────────────────────────────────
echo.
echo 🎉 설정 완료!
echo.
echo    다음 단계:
echo    1. run.ps1 파일을 실행하여 봇을 시작하세요
echo    2. 또는 명령 프롬프트에서 python main.py 실행
echo.
echo ─────────────────────────────────────────────────────────────
echo.

pause
