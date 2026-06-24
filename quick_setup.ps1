# 호요봇 빠른 설치 스크립트
Write-Host "🚀 호요봇 설치를 시작합니다...`n" -ForegroundColor Green

# Python 확인
Write-Host "1️⃣ Python 확인 중..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python이 설치되지 않았습니다!" -ForegroundColor Red
    Write-Host "   다음 링크에서 Python 3.11을 다운로드하세요:" -ForegroundColor Yellow
    Write-Host "   https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe`n" -ForegroundColor Yellow
    Read-Host "Enter를 눌러 종료"
    exit 1
}

# 프로젝트 폴더 확인
Write-Host "`n2️⃣ 프로젝트 폴더 확인 중..." -ForegroundColor Cyan
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
Write-Host "   ✅ 프로젝트 폴더: $(Get-Location)" -ForegroundColor Green

# pip 업그레이드
Write-Host "`n3️⃣ pip 업그레이드 중..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
Write-Host "   ✅ pip 업그레이드 완료" -ForegroundColor Green

# 패키지 설치
Write-Host "`n4️⃣ 필수 패키지 설치 중..." -ForegroundColor Cyan
Write-Host "   (이 작업은 몇 분 정도 걸릴 수 있습니다)" -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "   ✅ 필수 패키지 설치 완료" -ForegroundColor Green

Write-Host "`n5️⃣ 선택적 패키지 설치 중 (Hakushin)..." -ForegroundColor Cyan
try {
    pip install git+https://github.com/thesadru/hakushin.git
    Write-Host "   ✅ Hakushin 설치 완료" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Hakushin 설치 실패 (선택사항이므로 무시)" -ForegroundColor Yellow
}

# .env 파일 확인
Write-Host "`n6️⃣ 환경 변수 파일 확인 중..." -ForegroundColor Cyan
if (!(Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "   ⚠️ .env 파일이 생성되었습니다!" -ForegroundColor Yellow
        Write-Host "   Discord 토큰과 Gemini API 키를 입력해야 합니다." -ForegroundColor Yellow
        
        $openEnv = Read-Host "`n   지금 .env 파일을 열어서 설정하시겠습니까? (y/n)"
        if ($openEnv -eq 'y') {
            notepad .env
            Write-Host "`n   .env 파일을 저장하고 닫은 후 Enter를 누르세요..." -ForegroundColor Cyan
            Read-Host
        } else {
            Write-Host "`n   ⚠️ 나중에 .env 파일을 직접 편집해주세요!" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ .env.example 파일을 찾을 수 없습니다!" -ForegroundColor Red
        Write-Host "   수동으로 .env 파일을 생성해주세요." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ .env 파일이 이미 존재합니다" -ForegroundColor Green
}

# 설치 완료
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "✅ 설치가 완료되었습니다!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

Write-Host "📋 다음 단계:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1️⃣ 봇 테스트 실행:" -ForegroundColor Yellow
Write-Host "     python main.py" -ForegroundColor White
Write-Host ""
Write-Host "  2️⃣ 백그라운드 서비스 등록 (관리자 PowerShell 필요):" -ForegroundColor Yellow
Write-Host "     .\scripts\install_service.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  3️⃣ 봇 제어:" -ForegroundColor Yellow
Write-Host "     .\scripts\control_bot.ps1" -ForegroundColor White
Write-Host ""

$testRun = Read-Host "지금 봇을 테스트 실행하시겠습니까? (y/n)"
if ($testRun -eq 'y') {
    Write-Host "`n🤖 봇을 시작합니다... (종료하려면 Ctrl+C)`n" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Gray
    Write-Host ""
    python main.py
} else {
    Write-Host "`n👋 설치 스크립트를 종료합니다." -ForegroundColor Cyan
    Write-Host "   봇을 실행하려면: python main.py`n" -ForegroundColor White
}
