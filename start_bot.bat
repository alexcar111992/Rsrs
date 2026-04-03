@echo off
cd /d "%~dp0"
python run_bot.py
if errorlevel 1 (
    echo.
    echo Bot crashed or Python not found.
    echo Run install.bat first if you haven't.
    pause
)
