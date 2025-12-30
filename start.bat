@echo off
setlocal EnableDelayedExpansion

:: Change to script directory (handles Chinese paths)
cd /d "%~dp0"

:: Set console to UTF-8
chcp 65001 >nul 2>&1

title QuantVision v2.0 Launcher

echo.
echo ========================================
echo   QuantVision v2.0 - Starting...
echo ========================================
echo.

:: Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Startup failed. Check errors above.
    echo.
)

pause