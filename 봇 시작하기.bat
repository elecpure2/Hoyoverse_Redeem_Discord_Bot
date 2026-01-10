@echo off
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.11 or higher from: https://www.python.org/downloads/
    echo.
    echo Don't forget to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

python launcher.py
pause
