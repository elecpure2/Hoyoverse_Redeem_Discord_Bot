@echo off
chcp 65001 > nul
title 호요봇 시작하기

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              🎮 호요봇 시작하기 🎮                         ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM .env 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo.
    echo    먼저 "설정하기.bat"를 실행하여 설정을 완료하세요.
    echo.
    pause
    exit /b
)

REM Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다!
    echo.
    echo    Python 3.11을 설치해주세요:
    echo    https://www.python.org/downloads/
    echo.
    echo    ⚠️ 설치 시 "Add Python to PATH" 체크 필수!
    echo.
    pause
    exit /b
)

echo ✅ Python 확인 완료
echo.

REM 첫 실행 여부 확인 (venv 또는 설치 마커로 확인)
if not exist ".installed" (
    echo ─────────────────────────────────────────────────────────────
    echo.
    echo 📦 첫 실행 감지! 필요한 패키지를 설치합니다...
    echo    (이 과정은 최초 1회만 실행됩니다)
    echo.
    echo ─────────────────────────────────────────────────────────────
    echo.
    
    echo [1/2] 기본 패키지 설치 중...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ❌ 패키지 설치 실패!
        pause
        exit /b
    )
    echo.
    
    echo [2/2] Hakushin 라이브러리 설치 중...
    echo       (게임 데이터 조회에 필요)
    pip install git+https://github.com/thesadru/hakushin.git
    if errorlevel 1 (
        echo.
        echo ⚠️ Hakushin 설치 실패 - 일부 기능이 제한될 수 있습니다.
        echo    Git이 설치되어 있지 않으면 Hakushin을 설치할 수 없습니다.
        echo.
    )
    
    REM 설치 완료 마커 생성
    echo installed > .installed
    
    echo.
    echo ✅ 모든 패키지 설치 완료!
    echo.
)

echo ─────────────────────────────────────────────────────────────
echo.
echo 🚀 봇을 시작합니다...
echo.
echo    종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.
echo.
echo ─────────────────────────────────────────────────────────────
echo.

python main.py

echo.
echo ─────────────────────────────────────────────────────────────
echo.
echo 봇이 종료되었습니다.
echo.
pause
