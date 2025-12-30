@echo off
setlocal EnableDelayedExpansion

:: Change to script directory
cd /d "%~dp0"
chcp 65001 >nul 2>&1

title QuantVision v2.0

echo.
echo ========================================
echo   QuantVision v2.0 - Quick Start
echo ========================================
echo.

:: Check if venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] Backend virtual environment not found.
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)

:: Check if node_modules exists
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo [INFO] Starting Backend...
cd backend
start "QuantVision Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

:: Wait for backend to start
echo [INFO] Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [INFO] Starting Frontend...
cd frontend
start "QuantVision Frontend" cmd /k "npm run dev"
cd ..

:: Wait and open browser
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   WebSocket: ws://localhost:8000/ws/trading
echo.
echo   Close the CMD windows to stop services.
echo ========================================
echo.

:: Open browser
start http://localhost:5173

echo Press any key to exit this window...
pause >nul