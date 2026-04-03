@echo off
echo ============================================
echo   RSPS Bot Client - Installer for Windows
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install PyQt5 Pillow opencv-python numpy pyautogui pywin32 keyboard mouse mss requests
echo.

if errorlevel 1 (
    echo ERROR: Failed to install some packages.
    echo Try running this as Administrator.
    pause
    exit /b 1
)

echo ============================================
echo   Installation complete!
echo   Run the bot with: python run_bot.py
echo   Or double-click start_bot.bat
echo ============================================
pause
