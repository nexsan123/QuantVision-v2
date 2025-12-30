<#
.SYNOPSIS
    QuantVision v2.0 停止脚本

.DESCRIPTION
    停止所有 QuantVision 服务

.PARAMETER All
    停止全部服务（包括 Docker 容器）

.PARAMETER Docker
    只停止 Docker 容器

.PARAMETER Force
    强制终止所有相关进程
#>

[CmdletBinding()]
param(
    [switch]$All,
    [switch]$Docker,
    [switch]$Force
)

# ============================================================================
# 编码和路径修复
# ============================================================================
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

if ($PSScriptRoot) {
    Set-Location -LiteralPath $PSScriptRoot
}

$ErrorActionPreference = "Continue"
$script:ProjectRoot = $PSScriptRoot
$script:BackendPort = 8000
$script:FrontendPort = 5173

function Write-Status {
    param([string]$Status, [string]$Message)
    switch ($Status) {
        "OK" {
            Write-Host "  [OK] " -ForegroundColor Green -NoNewline
            Write-Host $Message
        }
        "FAIL" {
            Write-Host "  [X] " -ForegroundColor Red -NoNewline
            Write-Host $Message
        }
        "WAIT" {
            Write-Host "  [..] " -ForegroundColor Yellow -NoNewline
            Write-Host $Message
        }
        "INFO" {
            Write-Host "  [i] " -ForegroundColor Cyan -NoNewline
            Write-Host $Message
        }
        default {
            Write-Host "     $Message"
        }
    }
}

function Show-Banner {
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Magenta
    Write-Host "              QuantVision v2.0 - Stop Services                " -ForegroundColor Magenta
    Write-Host "==============================================================" -ForegroundColor Magenta
    Write-Host ""
}

function Stop-ProcessOnPort {
    param([int]$Port, [string]$ServiceName)

    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    $stopped = $false

    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            try {
                Stop-Process -Id $process.Id -Force -ErrorAction Stop
                $stopped = $true
            } catch {
                # Process may have already stopped
            }
        }
    }

    return $stopped
}

function Stop-BackendService {
    Write-Status "WAIT" "Stopping backend service..."

    # Stop by port
    if (Stop-ProcessOnPort $BackendPort "Backend") {
        Write-Status "OK" "Backend service stopped (port $BackendPort)"
        return
    }

    # Stop by process name
    $pythonProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    $stopped = $false
    foreach ($proc in $pythonProcs) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -match "uvicorn" -or $cmdLine -match "quantvision") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $stopped = $true
            }
        } catch {
            # Ignore errors
        }
    }

    if ($stopped) {
        Write-Status "OK" "Backend service stopped"
    } else {
        Write-Status "INFO" "Backend service not running"
    }
}

function Stop-FrontendService {
    Write-Status "WAIT" "Stopping frontend service..."

    # Stop by port
    if (Stop-ProcessOnPort $FrontendPort "Frontend") {
        Write-Status "OK" "Frontend service stopped (port $FrontendPort)"
        return
    }

    # Stop node processes related to vite/quantvision
    $nodeProcs = Get-Process -Name "node*" -ErrorAction SilentlyContinue
    $stopped = $false
    foreach ($proc in $nodeProcs) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -match "vite" -or $cmdLine -match "quantvision") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $stopped = $true
            }
        } catch {
            # Ignore errors
        }
    }

    if ($stopped) {
        Write-Status "OK" "Frontend service stopped"
    } else {
        Write-Status "INFO" "Frontend service not running"
    }
}

function Stop-DockerServices {
    Write-Status "WAIT" "Stopping Docker containers..."

    $composeFile = Join-Path $ProjectRoot "docker-compose.dev.yml"
    if (-not (Test-Path $composeFile)) {
        $composeFile = Join-Path $ProjectRoot "docker-compose.yml"
    }

    if (Test-Path $composeFile) {
        docker-compose -f $composeFile down 2>&1 | Out-Null
        Write-Status "OK" "Docker containers stopped"
    } else {
        # Try to stop containers directly
        $containers = @("quantvision-dev-postgres", "quantvision-dev-redis", "quantvision-postgres", "quantvision-redis")
        foreach ($container in $containers) {
            docker stop $container 2>&1 | Out-Null
        }
        Write-Status "OK" "Docker containers stopped"
    }
}

function Stop-AllForce {
    Write-Status "WAIT" "Force stopping all related processes..."

    # Stop by ports
    Stop-ProcessOnPort $BackendPort "Backend"
    Stop-ProcessOnPort $FrontendPort "Frontend"

    # Stop cmd processes that might be running our services
    $cmdProcs = Get-Process -Name "cmd" -ErrorAction SilentlyContinue
    foreach ($proc in $cmdProcs) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -match "uvicorn" -or $cmdLine -match "npm" -or $cmdLine -match "vite") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Ignore errors
        }
    }

    Write-Status "OK" "All processes force stopped"
}

# Main
Show-Banner

if ($Docker -and -not $All) {
    # Only stop Docker
    Stop-DockerServices
} elseif ($Force) {
    # Force stop all
    Stop-AllForce
    if ($All) {
        Stop-DockerServices
    }
} else {
    # Normal stop
    Stop-BackendService
    Stop-FrontendService

    if ($All) {
        Stop-DockerServices
    }
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  QuantVision services stopped                                " -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
