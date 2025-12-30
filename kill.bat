@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1

title QuantVision - Stop All

echo.
echo ========================================
echo   Stopping QuantVision Services...
echo ========================================
echo.

:: Kill node processes (frontend)
echo [INFO] Stopping frontend (node)...
taskkill /f /im node.exe 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Frontend stopped
) else (
    echo [INFO] No frontend process found
)

:: Kill python processes (backend)
echo [INFO] Stopping backend (python)...
for /f "tokens=2" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a 2>nul
)
echo [OK] Backend stopped

echo.
echo ========================================
echo   All services stopped.
echo ========================================
echo.

pause
