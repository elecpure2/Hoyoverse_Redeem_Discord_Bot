# 호요봇 제어 스크립트
# 사용법: .\control_bot.ps1

$taskName = "HoyoBot_AutoStart"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Menu {
    Clear-Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "            호요봇 제어 패널" -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 작업 스케줄러 상태 확인
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        $taskState = $task.State
        Write-Host "[작업 스케줄러 상태] " -NoNewline
        if ($taskState -eq "Running") {
            Write-Host "실행 중" -ForegroundColor Green
        } elseif ($taskState -eq "Ready") {
            Write-Host "대기 중" -ForegroundColor Yellow
        } else {
            Write-Host $taskState -ForegroundColor Gray
        }
    } else {
        Write-Host "[작업 스케줄러 상태] " -NoNewline
        Write-Host "등록되지 않음" -ForegroundColor Red
    }
    
    # Python 프로세스 확인
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*main.py*" -or $_.Path -like "*$scriptPath*"
    }
    Write-Host "[Python 프로세스] " -NoNewline
    if ($pythonProcesses) {
        Write-Host "$($pythonProcesses.Count)개 실행 중" -ForegroundColor Green
    } else {
        Write-Host "실행 중이지 않음" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 봇 시작 (수동)" -ForegroundColor White
    Write-Host "2. 봇 중지" -ForegroundColor White
    Write-Host "3. 봇 재시작" -ForegroundColor White
    Write-Host "4. 로그 보기 (bot.log)" -ForegroundColor White
    Write-Host "5. 에러 로그 보기 (bot_error.log)" -ForegroundColor White
    Write-Host "6. 로그 실시간 모니터링" -ForegroundColor White
    Write-Host "7. 작업 스케줄러 상태 확인" -ForegroundColor White
    Write-Host "0. 종료" -ForegroundColor White
    Write-Host ""
}

function Start-Bot {
    Write-Host "[*] 봇 시작 중..." -ForegroundColor Green
    
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Start-ScheduledTask -TaskName $taskName
        Start-Sleep -Seconds 2
        Write-Host "[OK] 시작 명령 전송 완료!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] 작업 스케줄러에 등록되지 않았습니다." -ForegroundColor Red
        Write-Host "먼저 install_service.ps1을 관리자 권한으로 실행하세요." -ForegroundColor Yellow
    }
    
    pause
}

function Stop-Bot {
    Write-Host "[*] 봇 중지 중..." -ForegroundColor Yellow
    
    # 작업 스케줄러 중지
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    }
    
    # Python 프로세스 강제 종료
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] 봇 프로세스 종료 완료!" -ForegroundColor Green
    } else {
        Write-Host "[WARN] 실행 중인 봇이 없습니다." -ForegroundColor Yellow
    }
    
    pause
}

function Restart-Bot {
    Write-Host "[*] 봇 재시작 중..." -ForegroundColor Cyan
    Stop-Bot
    Start-Sleep -Seconds 2
    Start-Bot
}

function Show-Log {
    param([string]$logFile)
    
    $logPath = Join-Path $scriptPath $logFile
    
    if (Test-Path $logPath) {
        Write-Host "[LOG] $logFile 내용 (최근 50줄):" -ForegroundColor Cyan
        Write-Host "================================================================================" -ForegroundColor Gray
        Get-Content $logPath -Tail 50 -Encoding UTF8
        Write-Host "================================================================================" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] 로그 파일을 찾을 수 없습니다: $logPath" -ForegroundColor Yellow
    }
    
    Write-Host ""
    pause
}

function Monitor-Log {
    $logPath = Join-Path $scriptPath "bot.log"
    
    if (Test-Path $logPath) {
        Write-Host "[*] 실시간 로그 모니터링 중... (Ctrl+C로 중지)" -ForegroundColor Cyan
        Write-Host "================================================================================" -ForegroundColor Gray
        Get-Content $logPath -Wait -Tail 20 -Encoding UTF8
    } else {
        Write-Host "[WARN] 로그 파일을 찾을 수 없습니다: $logPath" -ForegroundColor Yellow
        pause
    }
}

function Show-TaskStatus {
    Write-Host "[INFO] 작업 스케줄러 상세 정보:" -ForegroundColor Cyan
    Write-Host ""
    
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        $task | Format-List TaskName, State, Description
        
        $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
        if ($taskInfo) {
            Write-Host "마지막 실행 시간: $($taskInfo.LastRunTime)" -ForegroundColor Yellow
            Write-Host "마지막 실행 결과: $($taskInfo.LastTaskResult)" -ForegroundColor Yellow
            Write-Host "다음 실행 시간: $($taskInfo.NextRunTime)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[ERROR] 작업이 등록되지 않았습니다." -ForegroundColor Red
    }
    
    Write-Host ""
    pause
}

# 메인 루프
do {
    Show-Menu
    $choice = Read-Host "선택"
    
    switch ($choice) {
        "1" { Start-Bot }
        "2" { Stop-Bot }
        "3" { Restart-Bot }
        "4" { Show-Log "bot.log" }
        "5" { Show-Log "bot_error.log" }
        "6" { Monitor-Log }
        "7" { Show-TaskStatus }
        "0" { 
            Write-Host "[*] 종료합니다." -ForegroundColor Cyan
            break
        }
        default {
            Write-Host "[ERROR] 잘못된 선택입니다." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
} while ($choice -ne "0")
