@echo off
REM migasfree-connect installer for Windows
REM Run this script as Administrator

setlocal EnableDelayedExpansion

set "INSTALL_DIR=%PROGRAMDATA%\migasfree-connect"
set "SCRIPT_NAME=migasfree-connect"

echo.
echo ==========================================
echo   Migasfree Connect Installer for Windows
echo ==========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Right-click and select "Run as administrator".
    pause
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       Python %PYTHON_VERSION% found.

echo.
echo [2/4] Installing Python dependencies...
pip install --upgrade requests websockets urllib3
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [3/4] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo.
echo [4/4] Copying connect script...
copy /Y "%~dp0%SCRIPT_NAME%" "%INSTALL_DIR%\%SCRIPT_NAME%.py" >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy script.
    pause
    exit /b 1
)

REM Create batch wrapper for easy execution
echo @echo off > "%INSTALL_DIR%\%SCRIPT_NAME%.bat"
echo python "%%~dp0%SCRIPT_NAME%.py" %%* >> "%INSTALL_DIR%\%SCRIPT_NAME%.bat"

REM Add to PATH if not already there
echo.
echo Adding to PATH...
setx PATH "%PATH%;%INSTALL_DIR%" /M >nul 2>&1
if %errorlevel% equ 0 (
    echo       Added %INSTALL_DIR% to system PATH.
) else (
    echo       WARNING: Could not add to PATH. You may need to add manually.
)

echo.
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo Installation directory: %INSTALL_DIR%
echo.
echo Usage:
echo   migasfree-connect -t ssh -a CID-123 -m https://your-server root
echo.
echo NOTE: You may need to restart your terminal for PATH changes to take effect.
echo.
pause
