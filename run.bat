@echo off
echo Starting Khmer Dubbing Studio...

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Refresh PATH to pick up newly installed tools like FFmpeg
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSTEM_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SYSTEM_PATH%;%USER_PATH%"

call venv\Scripts\activate.bat
python main.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
