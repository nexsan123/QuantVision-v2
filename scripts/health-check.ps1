<#
.SYNOPSIS
    QuantVision v2.0 健康检查脚本

.DESCRIPTION
    检查所有服务的健康状态

.PARAMETER Verbose
    显示详细信息

.PARAMETER Json
    输出 JSON 格式

.PARAMETER Watch
    持续监控模式

.EXAMPLE
    .\health-check.ps1
    .\health-check.ps1 -Verbose
    .\health-check.ps1 -Watch

.NOTES
    作者: QuantVision Team
    版本: 2.0.0
#>

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Watch,
    [int]$Interval = 5
)

$script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$script:BackendPort = 8000
$script:FrontendPort = 5173

# 健康状态
$script:HealthStatus = @{
    timestamp = $null
    services = @{}
    overall = "unknown"
}

function Write-Status {
    param([string]$Status, [string]$Message, [string]$Detail = "")
    $icon = switch ($Status) {
        "OK" { "[32m✓[0m" }
        "FAIL" { "[31m✗[0m" }
        "WARN" { "[33m⚠[0m" }
        "INFO" { "[36mℹ[0m" }
        default { "  " }
    }
    Write-Host "  $icon $Message" -NoNewline
    if ($Detail) {
        Write-Host " [90m($Detail)[0m"
    } else {
        Write-Host ""
    }
}

function Test-ServiceHealth {
    param([string]$Name, [string]$Url, [int]$TimeoutSec = 5)

    $result = @{
        name = $Name
        status = "unknown"
        response_time = $null
        message = ""
    }

    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSec -ErrorAction Stop
        $stopwatch.Stop()

        $result.response_time = $stopwatch.ElapsedMilliseconds
        $result.status = if ($response.StatusCode -lt 400) { "healthy" } else { "degraded" }
        $result.message = "HTTP $($response.StatusCode)"
    } catch {
        $result.status = "unhealthy"
        $result.message = $_.Exception.Message
    }

    return $result
}

function Test-PortOpen {
    param([int]$Port)

    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Test-DockerContainer {
    param([string]$ContainerName)

    try {
        $status = docker inspect --format='{{.State.Status}}' $ContainerName 2>&1
        return @{
            status = if ($status -eq "running") { "healthy" } else { "unhealthy" }
            message = $status
        }
    } catch {
        return @{
            status = "unknown"
            message = "Container not found"
        }
    }
}

function Invoke-HealthCheck {
    $script:HealthStatus.timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $script:HealthStatus.services = @{}

    if (-not $Json) {
        Write-Host ""
        Write-Host "[35m╔══════════════════════════════════════════════════════════════╗[0m"
        Write-Host "[35m║              QuantVision v2.0 - 健康检查                     ║[0m"
        Write-Host "[35m╚══════════════════════════════════════════════════════════════╝[0m"
        Write-Host ""
        Write-Host "[36m[$($HealthStatus.timestamp)][0m"
        Write-Host ""
    }

    # ========================================================================
    # 后端 API
    # ========================================================================
    if (-not $Json) { Write-Host "[35m[后端服务][0m" }

    $backendHealth = Test-ServiceHealth -Name "Backend API" -Url "http://localhost:$BackendPort/api/v1/health"
    $script:HealthStatus.services["backend"] = $backendHealth

    if (-not $Json) {
        $detail = if ($backendHealth.response_time) { "$($backendHealth.response_time)ms" } else { "" }
        Write-Status $backendHealth.status.ToUpper() "后端 API (port $BackendPort)" $detail
    }

    # API 文档
    $docsHealth = Test-ServiceHealth -Name "API Docs" -Url "http://localhost:$BackendPort/docs"
    $script:HealthStatus.services["api_docs"] = $docsHealth

    if (-not $Json) {
        Write-Status $docsHealth.status.ToUpper() "API 文档 (/docs)"
    }

    # WebSocket
    $wsHealth = @{ status = "unknown"; message = "" }
    if (Test-PortOpen $BackendPort) {
        $wsHealth.status = "healthy"
        $wsHealth.message = "Port open"
    } else {
        $wsHealth.status = "unhealthy"
        $wsHealth.message = "Port closed"
    }
    $script:HealthStatus.services["websocket"] = $wsHealth

    if (-not $Json) {
        Write-Status $wsHealth.status.ToUpper() "WebSocket (ws://localhost:$BackendPort/ws)"
    }

    # ========================================================================
    # 前端
    # ========================================================================
    if (-not $Json) {
        Write-Host ""
        Write-Host "[35m[前端服务][0m"
    }

    $frontendHealth = Test-ServiceHealth -Name "Frontend" -Url "http://localhost:$FrontendPort"
    $script:HealthStatus.services["frontend"] = $frontendHealth

    if (-not $Json) {
        $detail = if ($frontendHealth.response_time) { "$($frontendHealth.response_time)ms" } else { "" }
        Write-Status $frontendHealth.status.ToUpper() "前端服务 (port $FrontendPort)" $detail
    }

    # ========================================================================
    # 数据库服务
    # ========================================================================
    if (-not $Json) {
        Write-Host ""
        Write-Host "[35m[数据库服务][0m"
    }

    # PostgreSQL
    $pgContainer = Test-DockerContainer "quantvision-dev-postgres"
    $script:HealthStatus.services["postgres"] = $pgContainer

    if (-not $Json) {
        if ($pgContainer.status -eq "healthy") {
            Write-Status "OK" "PostgreSQL (Docker)" "running"
        } elseif ($pgContainer.status -eq "unknown") {
            # 检查端口
            if (Test-PortOpen 5432) {
                Write-Status "OK" "PostgreSQL (port 5432)" "外部服务"
                $script:HealthStatus.services["postgres"].status = "healthy"
            } else {
                Write-Status "WARN" "PostgreSQL" "未运行"
            }
        } else {
            Write-Status "FAIL" "PostgreSQL" $pgContainer.message
        }
    }

    # Redis
    $redisContainer = Test-DockerContainer "quantvision-dev-redis"
    $script:HealthStatus.services["redis"] = $redisContainer

    if (-not $Json) {
        if ($redisContainer.status -eq "healthy") {
            Write-Status "OK" "Redis (Docker)" "running"
        } elseif ($redisContainer.status -eq "unknown") {
            if (Test-PortOpen 6379) {
                Write-Status "OK" "Redis (port 6379)" "外部服务"
                $script:HealthStatus.services["redis"].status = "healthy"
            } else {
                Write-Status "WARN" "Redis" "未运行"
            }
        } else {
            Write-Status "FAIL" "Redis" $redisContainer.message
        }
    }

    # ========================================================================
    # 总体状态
    # ========================================================================
    $healthyCount = ($HealthStatus.services.Values | Where-Object { $_.status -eq "healthy" }).Count
    $totalCount = $HealthStatus.services.Count

    if ($healthyCount -eq $totalCount) {
        $script:HealthStatus.overall = "healthy"
    } elseif ($healthyCount -gt 0) {
        $script:HealthStatus.overall = "degraded"
    } else {
        $script:HealthStatus.overall = "unhealthy"
    }

    if (-not $Json) {
        Write-Host ""
        Write-Host "[35m[总体状态][0m"
        $overallIcon = switch ($HealthStatus.overall) {
            "healthy" { "[32m✓ 所有服务正常[0m" }
            "degraded" { "[33m⚠ 部分服务异常[0m" }
            "unhealthy" { "[31m✗ 服务不可用[0m" }
            default { "[90m? 未知状态[0m" }
        }
        Write-Host "  $overallIcon ($healthyCount/$totalCount)"
        Write-Host ""
    }

    # JSON 输出
    if ($Json) {
        $HealthStatus | ConvertTo-Json -Depth 3
    }
}

# 主流程
if ($Watch) {
    Write-Host "开始持续监控 (间隔: ${Interval}s, 按 Ctrl+C 停止)"
    while ($true) {
        Clear-Host
        Invoke-HealthCheck
        Start-Sleep -Seconds $Interval
    }
} else {
    Invoke-HealthCheck
}
