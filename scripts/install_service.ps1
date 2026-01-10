# 이 스크립트는 관리자 권한으로 실행해야 합니다
# 사용법: PowerShell을 관리자 권한으로 열고 .\install_service.ps1 실행

# 관리자 권한 확인
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "이 스크립트는 관리자 권한이 필요합니다!"
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    pause
    exit
}

# 현재 스크립트 경로
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$vbsPath = Join-Path $scriptPath "start_bot_background.vbs"

# 작업 스케줄러에 등록
$taskName = "HoyoBot_AutoStart"
$description = "호요봇 자동 시작 서비스 (부팅 시 자동 실행)"

Write-Host "🔧 작업 스케줄러에 등록 중..." -ForegroundColor Cyan

# 기존 작업이 있으면 삭제
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "⚠️ 기존 작업 발견 - 삭제 후 재등록합니다." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# 작업 동작 설정 (VBS 스크립트 실행)
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`""

# 트리거 설정 (시스템 시작 시)
$trigger = New-ScheduledTaskTrigger -AtStartup

# 작업 주체 설정 (현재 사용자, 로그인 여부와 무관하게 실행)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited

# 작업 설정
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# 작업 등록
Register-ScheduledTask `
    -TaskName $taskName `
    -Description $description `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings | Out-Null

Write-Host "✅ 작업 스케줄러에 등록 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 작업 정보:" -ForegroundColor Cyan
Write-Host "  - 작업 이름: $taskName"
Write-Host "  - 실행 파일: $vbsPath"
Write-Host "  - 시작 조건: 시스템 부팅 시 자동 실행"
Write-Host ""
Write-Host "🎮 제어 명령어:" -ForegroundColor Yellow
Write-Host "  - 수동 시작: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  - 중지: Stop-ScheduledTask -TaskName '$taskName' (후 taskkill /F /IM python.exe)"
Write-Host "  - 삭제: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
Write-Host ""
Write-Host "📄 로그 확인:" -ForegroundColor Yellow
Write-Host "  - 로그 파일: $scriptPath\bot.log"
Write-Host "  - 에러 로그: $scriptPath\bot_error.log"
Write-Host ""
Write-Host "💡 팁: 지금 바로 시작하려면 다음 명령어를 실행하세요:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host ""

pause




