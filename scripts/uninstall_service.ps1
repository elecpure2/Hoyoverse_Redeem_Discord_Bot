# 작업 스케줄러에서 호요봇 제거
# 사용법: PowerShell을 관리자 권한으로 열고 .\uninstall_service.ps1 실행

# 관리자 권한 확인
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "이 스크립트는 관리자 권한이 필요합니다!"
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    pause
    exit
}

$taskName = "HoyoBot_AutoStart"

Write-Host "🛑 작업 스케줄러에서 제거 중..." -ForegroundColor Cyan

# 실행 중인 봇 프로세스 종료
Write-Host "봇 프로세스 종료 중..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$env:USERNAME*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 작업 스케줄러에서 제거
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "✅ 제거 완료!" -ForegroundColor Green
} else {
    Write-Host "⚠️ 등록된 작업을 찾을 수 없습니다." -ForegroundColor Yellow
}

Write-Host ""
pause




