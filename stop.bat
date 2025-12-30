@echo off
setlocal EnableDelayedExpansion

:: Change to script directory
cd /d "%~dp0"

:: Set console to UTF-8
chcp 65001 >nul 2>&1

title QuantVision v2.0 - Stop Services

echo.
echo ========================================
echo   QuantVision v2.0 - Stopping...
echo ========================================
echo.

:: Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File ".\stop.ps1" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Stop failed. Check errors above.
    echo.
)

pause