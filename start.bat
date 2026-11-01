@echo off
cd /d "%~dp0"

if exist "LiveTranslate.exe" (
    start "" "%~dp0LiveTranslate.exe" %*
    exit /b 0
)

set PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\.livetranslate-ready" (
    echo [ERROR] Virtual environment setup is incomplete.
    echo Please run install.bat again to finish installing and verifying dependencies.
    echo.
    pause
    exit /b 1
)

echo Starting LiveTranslate...
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py %*
) else (
    .venv\Scripts\python.exe main.py %*
)
