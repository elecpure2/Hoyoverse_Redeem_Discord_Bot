$ErrorActionPreference = "Stop"

# 현재 스크립트의 경로 (scripts 폴더)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 실행할 VBS 파일의 절대 경로
$targetPath = Join-Path $scriptPath "start_bot_background.vbs"
if (-not (Test-Path $targetPath)) {
    Write-Error "Could not find start_bot_background.vbs at $targetPath"
}
$targetPath = (Get-Item $targetPath).FullName

# 시작 프로그램 폴더 경로
$startupFolderPath = [System.Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolderPath "HoyoBot_AutoStart.lnk"

# 바로가기 생성
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
# 작업 디렉토리를 프로젝트 루트로 설정 (scripts 폴더의 상위)
$shortcut.WorkingDirectory = (Split-Path -Parent $scriptPath)
$shortcut.Description = "Hoyo Bot Auto Start"
$shortcut.Save()

Write-Host "✅ 시작 프로그램에 바로가기가 생성되었습니다:" -ForegroundColor Green
Write-Host "   $shortcutPath" -ForegroundColor Gray
Write-Host "   Target: $targetPath" -ForegroundColor Gray
