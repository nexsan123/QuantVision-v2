<#
.SYNOPSIS
    QuantVision v2.0 一键启动脚本

.DESCRIPTION
    自动检查环境、安装依赖、启动所有服务

.PARAMETER BackendOnly
    只启动后端服务

.PARAMETER FrontendOnly
    只启动前端服务

.PARAMETER WithDocker
    同时启动 Docker 数据库服务

.PARAMETER Install
    强制重新安装依赖

.PARAMETER NoBrowser
    不自动打开浏览器

.PARAMETER Production
    生产模式（构建后预览）

.EXAMPLE
    .\start.ps1
    .\start.ps1 -BackendOnly
    .\start.ps1 -WithDocker -Install
#>

[CmdletBinding()]
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$WithDocker,
    [switch]$Install,
    [switch]$NoBrowser,
    [switch]$Production
)

# ============================================================================
# 编码和路径修复
# ============================================================================
# Fix Chinese path encoding issues
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# Change to script directory (critical for Chinese paths)
if ($PSScriptRoot) {
    Set-Location -LiteralPath $PSScriptRoot
}

# Verify we're in the correct directory
if (-not (Test-Path ".\backend") -or -not (Test-Path ".\frontend")) {
    Write-Host "[ERROR] Cannot find backend/frontend directories." -ForegroundColor Red
    Write-Host "Current path: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 配置
# ============================================================================
$ErrorActionPreference = "Stop"
$script:ProjectRoot = $PSScriptRoot
$script:BackendDir = Join-Path $ProjectRoot "backend"
$script:FrontendDir = Join-Path $ProjectRoot "frontend"
$script:LogsDir = Join-Path $ProjectRoot "logs"
$script:ScriptsDir = Join-Path $ProjectRoot "scripts"

$script:BackendPort = 8000
$script:FrontendPort = 5173
$script:DateStr = Get-Date -Format "yyyy-MM-dd"

# ============================================================================
# 工具函数
# ============================================================================
function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    switch ($Status) {
        "OK" {
            Write-Host "  " -NoNewline
            Write-Host "[OK]" -ForegroundColor Green -NoNewline
            Write-Host " $Message"
        }
        "FAIL" {
            Write-Host "  " -NoNewline
            Write-Host "[X]" -ForegroundColor Red -NoNewline
            Write-Host " $Message"
        }
        "WAIT" {
            Write-Host "  " -NoNewline
            Write-Host "[..]" -ForegroundColor Yellow -NoNewline
            Write-Host " $Message"
        }
        "INFO" {
            Write-Host "  " -NoNewline
            Write-Host "[i]" -ForegroundColor Cyan -NoNewline
            Write-Host " $Message"
        }
        default {
            Write-Host "     $Message"
        }
    }
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "[$Title]" -ForegroundColor Magenta
}

function Show-Banner {
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Magenta
    Write-Host "                                                              " -ForegroundColor Magenta
    Write-Host "     QQQQQ   U   U   AAAAA   N   N   TTTTT                   " -ForegroundColor Magenta
    Write-Host "    Q     Q  U   U  A     A  NN  N     T                     " -ForegroundColor Magenta
    Write-Host "    Q     Q  U   U  AAAAAAA  N N N     T                     " -ForegroundColor Magenta
    Write-Host "    Q   Q Q  U   U  A     A  N  NN     T                     " -ForegroundColor Magenta
    Write-Host "     QQQQQ Q  UUU   A     A  N   N     T                     " -ForegroundColor Magenta
    Write-Host "                                                              " -ForegroundColor Magenta
    Write-Host "              QuantVision v2.0 Launcher                       " -ForegroundColor Cyan
    Write-Host "                                                              " -ForegroundColor Magenta
    Write-Host "==============================================================" -ForegroundColor Magenta
    Write-Host ""
}

function Show-CompleteBanner {
    $mode = if ($Production) { "Production" } else { "Development" }
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Green
    Write-Host "  QuantVision Started! ($mode)                    " -ForegroundColor Green
    Write-Host "==============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Frontend:     " -NoNewline
    Write-Host "http://localhost:$FrontendPort" -ForegroundColor Cyan
    Write-Host "  Backend API:  " -NoNewline
    Write-Host "http://localhost:$BackendPort" -ForegroundColor Cyan
    Write-Host "  API Docs:     " -NoNewline
    Write-Host "http://localhost:$BackendPort/docs" -ForegroundColor Cyan
    Write-Host "  WebSocket:    " -NoNewline
    Write-Host "ws://localhost:$BackendPort/ws/trading" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Logs:" -ForegroundColor Gray
    Write-Host "    Backend:  logs/backend-$DateStr.log" -ForegroundColor Gray
    Write-Host "    Frontend: logs/frontend-$DateStr.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Press Ctrl+C or run .\stop.ps1 to stop services" -ForegroundColor Yellow
    Write-Host "==============================================================" -ForegroundColor Green
    Write-Host ""
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Get-VersionNumber {
    param([string]$Command, [string]$VersionArg = "--version")
    try {
        $output = & $Command $VersionArg 2>&1
        if ($output -match '(\d+\.\d+(\.\d+)?)') {
            return $Matches[1]
        }
    } catch {
        return $null
    }
    return $null
}

function Test-Port {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Stop-ProcessOnPort {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            Write-Status "INFO" "Stopping process on port $Port : $($process.ProcessName) (PID: $($process.Id))"
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60,
        [int]$IntervalMs = 1000
    )
    $elapsed = 0
    while ($elapsed -lt ($TimeoutSeconds * 1000)) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            # Continue waiting
        }
        Start-Sleep -Milliseconds $IntervalMs
        $elapsed += $IntervalMs
    }
    return $false
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

# ============================================================================
# Environment Check
# ============================================================================
function Test-Environment {
    Write-Section "Environment Check"
    $allOk = $true

    # Python check
    if (Test-Command "python") {
        $pyVersion = Get-VersionNumber "python" "--version"
        if ($pyVersion -and [version]$pyVersion -ge [version]"3.11") {
            Write-Status "OK" "Python $pyVersion installed"
        } else {
            Write-Status "FAIL" "Python version too low: $pyVersion (need 3.11+)"
            $allOk = $false
        }
    } else {
        Write-Status "FAIL" "Python not installed"
        Write-Host "    Install: https://www.python.org/downloads/" -ForegroundColor Gray
        $allOk = $false
    }

    # Node.js check
    if (Test-Command "node") {
        $nodeVersion = Get-VersionNumber "node" "--version"
        $nodeVersion = $nodeVersion -replace '^v', ''
        if ($nodeVersion -and [version]$nodeVersion -ge [version]"18.0") {
            Write-Status "OK" "Node.js v$nodeVersion installed"
        } else {
            Write-Status "FAIL" "Node.js version too low: $nodeVersion (need 18+)"
            $allOk = $false
        }
    } else {
        Write-Status "FAIL" "Node.js not installed"
        Write-Host "    Install: https://nodejs.org/" -ForegroundColor Gray
        $allOk = $false
    }

    # npm check
    if (Test-Command "npm") {
        $npmVersion = Get-VersionNumber "npm" "--version"
        Write-Status "OK" "npm $npmVersion installed"
    } else {
        Write-Status "FAIL" "npm not installed"
        $allOk = $false
    }

    # Docker check (optional)
    if ($WithDocker) {
        if (Test-Command "docker") {
            try {
                $dockerInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "OK" "Docker Desktop running"
                } else {
                    Write-Status "FAIL" "Docker Desktop not running"
                    Write-Host "    Please start Docker Desktop" -ForegroundColor Gray
                    $allOk = $false
                }
            } catch {
                Write-Status "FAIL" "Docker check failed"
                $allOk = $false
            }
        } else {
            Write-Status "FAIL" "Docker not installed"
            $allOk = $false
        }
    } else {
        if (Test-Command "docker") {
            Write-Status "INFO" "Docker available (use -WithDocker to start database)"
        }
    }

    return $allOk
}

# ============================================================================
# Dependencies Check
# ============================================================================
function Test-Dependencies {
    Write-Section "Dependencies Check"

    $venvPath = Join-Path $BackendDir "venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"

    if (-not $FrontendOnly) {
        if (Test-Path $venvPython) {
            if (-not $Install) {
                Write-Status "OK" "Backend virtual environment ready (venv)"
            }
        } else {
            Write-Status "WAIT" "Creating backend virtual environment..."
            Push-Location $BackendDir
            python -m venv venv
            Pop-Location
            Write-Status "OK" "Backend virtual environment created"
        }

        # Check backend dependencies
        $requirementsFile = Join-Path $BackendDir "requirements.txt"
        if ($Install -or -not (Test-Path (Join-Path $venvPath "Lib\site-packages\fastapi"))) {
            Write-Status "WAIT" "Installing backend dependencies..."
            Push-Location $BackendDir
            & $venvPython -m pip install --upgrade pip -q 2>&1 | Out-Null
            & $venvPython -m pip install -r requirements.txt -q 2>&1 | Out-Null
            Pop-Location
            Write-Status "OK" "Backend dependencies installed"
        } else {
            Write-Status "OK" "Backend dependencies ready (requirements.txt)"
        }
    }

    # Frontend dependencies
    if (-not $BackendOnly) {
        $nodeModules = Join-Path $FrontendDir "node_modules"
        if ($Install -or -not (Test-Path $nodeModules)) {
            Write-Status "WAIT" "Installing frontend dependencies..."
            Push-Location $FrontendDir
            npm install --silent 2>&1 | Out-Null
            Pop-Location
            Write-Status "OK" "Frontend dependencies installed"
        } else {
            Write-Status "OK" "Frontend dependencies ready (node_modules)"
        }
    }

    # Check .env file
    $envFile = Join-Path $ProjectRoot ".env"
    $envExample = Join-Path $ProjectRoot ".env.example"
    if (-not (Test-Path $envFile)) {
        if (Test-Path $envExample) {
            Copy-Item $envExample $envFile
            Write-Status "INFO" "Created .env from .env.example"
            Write-Host "    Please edit .env file to configure API keys" -ForegroundColor Gray
        }
    }
}

# ============================================================================
# Docker Services
# ============================================================================
function Start-DockerServices {
    if (-not $WithDocker) { return }

    Write-Section "Starting Docker Services"

    $composeFile = Join-Path $ProjectRoot "docker-compose.dev.yml"
    if (-not (Test-Path $composeFile)) {
        $composeFile = Join-Path $ProjectRoot "docker-compose.yml"
    }

    if (Test-Path $composeFile) {
        Write-Status "WAIT" "Starting PostgreSQL (Docker)..."
        docker-compose -f $composeFile up -d postgres 2>&1 | Out-Null
        Write-Status "OK" "PostgreSQL started"

        Write-Status "WAIT" "Starting Redis (Docker)..."
        docker-compose -f $composeFile up -d redis 2>&1 | Out-Null
        Write-Status "OK" "Redis started"

        # Wait for database ready
        Write-Status "WAIT" "Waiting for database ready..."
        Start-Sleep -Seconds 3
    } else {
        Write-Status "FAIL" "docker-compose file not found"
    }
}

# ============================================================================
# Start Services
# ============================================================================
function Start-Backend {
    Write-Status "WAIT" "Starting backend service (port $BackendPort)..."

    # Check port
    if (Test-Port $BackendPort) {
        Write-Status "INFO" "Port $BackendPort in use, releasing..."
        Stop-ProcessOnPort $BackendPort
        Start-Sleep -Seconds 1
    }

    $venvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
    $logFile = Join-Path $LogsDir "backend-$DateStr.log"
    $errLogFile = Join-Path $LogsDir "backend-$DateStr.err.log"

    # Start backend using cmd to combine stdout and stderr
    $script:BackendProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "`"$venvPython`" -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --reload > `"$logFile`" 2>&1" `
        -WorkingDirectory $BackendDir `
        -WindowStyle Minimized `
        -PassThru

    # Wait for service ready
    $ready = Wait-ForService "http://localhost:$BackendPort/api/v1/health" -TimeoutSeconds 30
    if ($ready) {
        Write-Status "OK" "Backend service started (PID: $($BackendProcess.Id))"
    } else {
        Write-Status "FAIL" "Backend service start timeout"
        Write-Host "    Check log: $logFile" -ForegroundColor Gray
    }
}

function Start-Frontend {
    Write-Status "WAIT" "Starting frontend service (port $FrontendPort)..."

    # Check port
    if (Test-Port $FrontendPort) {
        Write-Status "INFO" "Port $FrontendPort in use, releasing..."
        Stop-ProcessOnPort $FrontendPort
        Start-Sleep -Seconds 1
    }

    $logFile = Join-Path $LogsDir "frontend-$DateStr.log"

    if ($Production) {
        # Production mode: build then preview
        Write-Status "WAIT" "Building frontend..."
        Push-Location $FrontendDir
        npm run build 2>&1 | Out-Null
        Pop-Location

        $script:FrontendProcess = Start-Process -FilePath "cmd.exe" `
            -ArgumentList "/c", "npm run preview -- --port $FrontendPort > `"$logFile`" 2>&1" `
            -WorkingDirectory $FrontendDir `
            -WindowStyle Minimized `
            -PassThru
    } else {
        # Development mode
        $script:FrontendProcess = Start-Process -FilePath "cmd.exe" `
            -ArgumentList "/c", "npm run dev -- --port $FrontendPort > `"$logFile`" 2>&1" `
            -WorkingDirectory $FrontendDir `
            -WindowStyle Minimized `
            -PassThru
    }

    # Wait for service ready
    Start-Sleep -Seconds 3
    Write-Status "OK" "Frontend service started (PID: $($FrontendProcess.Id))"
}

# ============================================================================
# Health Check
# ============================================================================
function Test-Health {
    Write-Section "Health Check"

    if (-not $FrontendOnly) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$BackendPort/api/v1/health" -TimeoutSec 5
            if ($response.status -eq "healthy") {
                Write-Status "OK" "Backend API healthy"
            } else {
                Write-Status "INFO" "Backend API status: $($response.status)"
            }
        } catch {
            Write-Status "FAIL" "Backend API not responding"
        }
    }

    if ($WithDocker) {
        # Check database
        try {
            $dbCheck = docker exec quantvision-dev-postgres pg_isready -U quantvision 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "OK" "Database connection OK"
            } else {
                Write-Status "FAIL" "Database connection failed"
            }
        } catch {
            Write-Status "INFO" "Database check skipped"
        }

        # Check Redis
        try {
            $redisCheck = docker exec quantvision-dev-redis redis-cli ping 2>&1
            if ($redisCheck -eq "PONG") {
                Write-Status "OK" "Redis connection OK"
            } else {
                Write-Status "FAIL" "Redis connection failed"
            }
        } catch {
            Write-Status "INFO" "Redis check skipped"
        }
    }
}

# ============================================================================
# Main
# ============================================================================
function Main {
    # Ensure log directory exists
    Ensure-Directory $LogsDir

    # Show banner
    Show-Banner

    # Environment check
    $envOk = Test-Environment
    if (-not $envOk) {
        Write-Host ""
        Write-Host "Environment check failed. Please install missing dependencies." -ForegroundColor Red
        exit 1
    }

    # Dependencies check
    Test-Dependencies

    # Docker services
    Start-DockerServices

    # Start services
    Write-Section "Starting Services"

    if (-not $FrontendOnly) {
        Start-Backend
    }

    if (-not $BackendOnly) {
        Start-Frontend
    }

    # Health check
    Test-Health

    # Show complete info
    Show-CompleteBanner

    # Open browser
    if (-not $NoBrowser -and -not $BackendOnly) {
        Write-Host "Opening browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:$FrontendPort"
    }

    # Keep script running
    Write-Host ""
    Write-Host "Press any key to exit (services will continue running in background)..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Run main function
try {
    Main
} catch {
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
