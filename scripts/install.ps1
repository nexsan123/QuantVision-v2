<#
.SYNOPSIS
    QuantVision v2.0 依赖安装脚本

.DESCRIPTION
    安装后端和前端依赖，初始化数据库

.PARAMETER Backend
    只安装后端依赖

.PARAMETER Frontend
    只安装前端依赖

.PARAMETER InitDB
    初始化数据库

.PARAMETER Force
    强制重新安装（删除现有环境）

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Backend
    .\install.ps1 -InitDB

.NOTES
    作者: QuantVision Team
    版本: 2.0.0
#>

[CmdletBinding()]
param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$InitDB,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$script:BackendDir = Join-Path $ProjectRoot "backend"
$script:FrontendDir = Join-Path $ProjectRoot "frontend"

# 颜色输出
function Write-Status {
    param([string]$Status, [string]$Message)
    $icon = switch ($Status) {
        "OK" { "[32m✓[0m" }
        "FAIL" { "[31m✗[0m" }
        "WAIT" { "[33m⏳[0m" }
        "INFO" { "[36mℹ[0m" }
        default { "  " }
    }
    Write-Host "  $icon $Message"
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "[35m[$Title][0m"
}

# Banner
Write-Host ""
Write-Host "[35m╔══════════════════════════════════════════════════════════════╗[0m"
Write-Host "[35m║              QuantVision v2.0 - 依赖安装                     ║[0m"
Write-Host "[35m╚══════════════════════════════════════════════════════════════╝[0m"
Write-Host ""

$installBackend = -not $Frontend -or $Backend
$installFrontend = -not $Backend -or $Frontend

# ============================================================================
# 后端安装
# ============================================================================
if ($installBackend) {
    Write-Section "安装后端依赖"

    $venvPath = Join-Path $BackendDir "venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"

    # 强制模式：删除现有环境
    if ($Force -and (Test-Path $venvPath)) {
        Write-Status "WAIT" "删除现有虚拟环境..."
        Remove-Item -Path $venvPath -Recurse -Force
    }

    # 创建虚拟环境
    if (-not (Test-Path $venvPython)) {
        Write-Status "WAIT" "创建 Python 虚拟环境..."
        Push-Location $BackendDir
        python -m venv venv
        Pop-Location
        Write-Status "OK" "虚拟环境创建完成"
    } else {
        Write-Status "OK" "虚拟环境已存在"
    }

    # 升级 pip
    Write-Status "WAIT" "升级 pip..."
    & $venvPython -m pip install --upgrade pip -q

    # 安装依赖
    Write-Status "WAIT" "安装 Python 依赖..."
    $requirementsFile = Join-Path $BackendDir "requirements.txt"
    if (Test-Path $requirementsFile) {
        & $venvPython -m pip install -r $requirementsFile -q
        Write-Status "OK" "Python 依赖安装完成"
    } else {
        Write-Status "FAIL" "未找到 requirements.txt"
    }

    # 安装开发依赖
    $devRequirements = Join-Path $BackendDir "requirements-dev.txt"
    if (Test-Path $devRequirements) {
        Write-Status "WAIT" "安装开发依赖..."
        & $venvPython -m pip install -r $devRequirements -q
        Write-Status "OK" "开发依赖安装完成"
    }
}

# ============================================================================
# 前端安装
# ============================================================================
if ($installFrontend) {
    Write-Section "安装前端依赖"

    $nodeModules = Join-Path $FrontendDir "node_modules"

    # 强制模式：删除现有依赖
    if ($Force -and (Test-Path $nodeModules)) {
        Write-Status "WAIT" "删除现有 node_modules..."
        Remove-Item -Path $nodeModules -Recurse -Force
    }

    # 安装依赖
    Write-Status "WAIT" "安装 npm 依赖..."
    Push-Location $FrontendDir

    # 使用 npm ci (更快、更严格) 或 npm install
    if (Test-Path (Join-Path $FrontendDir "package-lock.json")) {
        npm ci --silent 2>&1 | Out-Null
    } else {
        npm install --silent 2>&1 | Out-Null
    }

    Pop-Location
    Write-Status "OK" "npm 依赖安装完成"
}

# ============================================================================
# 环境变量配置
# ============================================================================
Write-Section "环境配置"

$envFile = Join-Path $ProjectRoot ".env"
$envExample = Join-Path $ProjectRoot ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Status "OK" "已从 .env.example 创建 .env 文件"
        Write-Host "    [33m请编辑 .env 文件配置 API 密钥[0m"
    } else {
        Write-Status "FAIL" "未找到 .env.example 模板"
    }
} else {
    Write-Status "OK" ".env 文件已存在"
}

# ============================================================================
# 数据库初始化
# ============================================================================
if ($InitDB) {
    Write-Section "初始化数据库"

    # 检查 Docker
    $dockerRunning = $false
    try {
        docker info 2>&1 | Out-Null
        $dockerRunning = $true
    } catch {
        $dockerRunning = $false
    }

    if ($dockerRunning) {
        Write-Status "WAIT" "启动数据库容器..."
        $composeFile = Join-Path $ProjectRoot "docker-compose.dev.yml"
        if (Test-Path $composeFile) {
            docker-compose -f $composeFile up -d postgres redis 2>&1 | Out-Null
            Start-Sleep -Seconds 5
            Write-Status "OK" "数据库容器已启动"
        }

        # 运行数据库迁移
        Write-Status "WAIT" "运行数据库迁移..."
        $venvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            Push-Location $BackendDir
            try {
                & $venvPython -c "from app.core.database import init_db; init_db()"
                Write-Status "OK" "数据库迁移完成"
            } catch {
                Write-Status "INFO" "数据库迁移跳过（可能需要手动执行）"
            }
            Pop-Location
        }
    } else {
        Write-Status "FAIL" "Docker 未运行，无法初始化数据库"
        Write-Host "    请启动 Docker Desktop 后重试"
    }
}

# ============================================================================
# 完成
# ============================================================================
Write-Host ""
Write-Host "[32m╔══════════════════════════════════════════════════════════════╗[0m"
Write-Host "[32m║  安装完成!                                                   ║[0m"
Write-Host "[32m╠══════════════════════════════════════════════════════════════╣[0m"
Write-Host "[32m║                                                              ║[0m"
Write-Host "[32m║  下一步:                                                     ║[0m"
Write-Host "[32m║    1. 编辑 .env 文件配置 API 密钥                            ║[0m"
Write-Host "[32m║    2. 运行 [36m.\start.ps1[32m 启动服务                              ║[0m"
Write-Host "[32m║                                                              ║[0m"
Write-Host "[32m╚══════════════════════════════════════════════════════════════╝[0m"
Write-Host ""
