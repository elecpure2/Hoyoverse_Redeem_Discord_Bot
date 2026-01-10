# Cursor 터미널에서 실행하는 간단한 스크립트
# 사용법: .\run.ps1
# 이 스크립트는 Cursor 터미널에서 직접 실행하여 로그를 볼 수 있습니다.

# 환경 변수 설정
# .env 파일에서 자동으로 로드됩니다.

# 작업 디렉토리 확인
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🚀 봇 시작 중..." -ForegroundColor Green
Write-Host "경로: $(Get-Location)\main.py" -ForegroundColor Cyan
Write-Host "환경 변수 설정 완료!" -ForegroundColor Cyan
Write-Host ""
Write-Host "로그가 아래에 표시됩니다. 종료하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host ""

# 필요한 패키지 설치
# py -3.11 -m pip install -r requirements.txt

# 봇 실행
py -3.11 main.py
