@echo off
REM migasfree-connect uninstaller for Windows
REM Run this script as Administrator

setlocal EnableDelayedExpansion

set "INSTALL_DIR=%PROGRAMDATA%\migasfree-connect"

echo.
echo ============================================
echo   Migasfree Connect Uninstaller for Windows
echo ============================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Right-click and select "Run as administrator".
    pause
    exit /b 1
)

echo [1/2] Removing installation directory...
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo       Directory removed.
) else (
    echo       Directory not found, skipping.
)

echo.
echo [2/2] Done.
echo.
echo ============================================
echo   Uninstallation Complete!
echo ============================================
echo.
echo NOTE: Python dependencies were not removed.
echo If you want to remove them, run:
echo   pip uninstall requests websockets urllib3
echo.
echo NOTE: The PATH entry was not removed automatically.
echo You may want to remove %INSTALL_DIR% from your system PATH.
echo.
pause
