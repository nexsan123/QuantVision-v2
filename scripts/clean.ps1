<#
.SYNOPSIS
    QuantVision v2.0 清理脚本

.DESCRIPTION
    清理缓存、临时文件和构建产物

.PARAMETER All
    清理所有内容（包括依赖）

.PARAMETER Cache
    只清理缓存

.PARAMETER Build
    只清理构建产物

.PARAMETER Logs
    清理日志文件

.PARAMETER Dependencies
    清理依赖（venv, node_modules）

.PARAMETER DryRun
    预览模式，不实际删除

.EXAMPLE
    .\clean.ps1
    .\clean.ps1 -All
    .\clean.ps1 -Logs -DryRun

.NOTES
    作者: QuantVision Team
    版本: 2.0.0
#>

[CmdletBinding()]
param(
    [switch]$All,
    [switch]$Cache,
    [switch]$Build,
    [switch]$Logs,
    [switch]$Dependencies,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$script:BackendDir = Join-Path $ProjectRoot "backend"
$script:FrontendDir = Join-Path $ProjectRoot "frontend"
$script:LogsDir = Join-Path $ProjectRoot "logs"

$script:TotalSize = 0
$script:TotalItems = 0

function Write-Status {
    param([string]$Status, [string]$Message)
    $icon = switch ($Status) {
        "OK" { "[32m✓[0m" }
        "FAIL" { "[31m✗[0m" }
        "WAIT" { "[33m⏳[0m" }
        "INFO" { "[36mℹ[0m" }
        "SKIP" { "[90m○[0m" }
        default { "  " }
    }
    Write-Host "  $icon $Message"
}

function Format-Size {
    param([long]$Size)
    if ($Size -ge 1GB) { return "{0:N2} GB" -f ($Size / 1GB) }
    if ($Size -ge 1MB) { return "{0:N2} MB" -f ($Size / 1MB) }
    if ($Size -ge 1KB) { return "{0:N2} KB" -f ($Size / 1KB) }
    return "$Size B"
}

function Remove-ItemSafe {
    param(
        [string]$Path,
        [string]$Description
    )

    if (Test-Path $Path) {
        $item = Get-Item $Path -ErrorAction SilentlyContinue
        $size = 0

        if ($item.PSIsContainer) {
            $size = (Get-ChildItem $Path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        } else {
            $size = $item.Length
        }

        $script:TotalSize += $size
        $script:TotalItems++

        if ($DryRun) {
            Write-Status "INFO" "$Description ($(Format-Size $size))"
        } else {
            try {
                Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
                Write-Status "OK" "$Description ($(Format-Size $size))"
            } catch {
                Write-Status "FAIL" "无法删除: $Description"
            }
        }
    } else {
        Write-Status "SKIP" "$Description (不存在)"
    }
}

# Banner
Write-Host ""
Write-Host "[35m╔══════════════════════════════════════════════════════════════╗[0m"
Write-Host "[35m║              QuantVision v2.0 - 清理工具                     ║[0m"
Write-Host "[35m╚══════════════════════════════════════════════════════════════╝[0m"
Write-Host ""

if ($DryRun) {
    Write-Host "[33m[预览模式] 以下内容将被清理（不会实际删除）:[0m"
    Write-Host ""
}

# 如果没有指定任何选项，默认清理缓存和构建产物
if (-not ($All -or $Cache -or $Build -or $Logs -or $Dependencies)) {
    $Cache = $true
    $Build = $true
}

if ($All) {
    $Cache = $true
    $Build = $true
    $Logs = $true
    $Dependencies = $true
}

# ============================================================================
# 清理 Python 缓存
# ============================================================================
if ($Cache) {
    Write-Host "[35m[Python 缓存][0m"

    # __pycache__ 目录
    $pycacheDirs = Get-ChildItem -Path $BackendDir -Filter "__pycache__" -Directory -Recurse -ErrorAction SilentlyContinue
    foreach ($dir in $pycacheDirs) {
        Remove-ItemSafe -Path $dir.FullName -Description "__pycache__: $($dir.Parent.Name)"
    }

    # .pyc 文件
    $pycFiles = Get-ChildItem -Path $BackendDir -Filter "*.pyc" -File -Recurse -ErrorAction SilentlyContinue
    if ($pycFiles.Count -gt 0) {
        foreach ($file in $pycFiles) {
            Remove-ItemSafe -Path $file.FullName -Description ".pyc: $($file.Name)"
        }
    }

    # .pytest_cache
    Remove-ItemSafe -Path (Join-Path $BackendDir ".pytest_cache") -Description "pytest 缓存"

    # mypy_cache
    Remove-ItemSafe -Path (Join-Path $BackendDir ".mypy_cache") -Description "mypy 缓存"

    Write-Host ""
}

# ============================================================================
# 清理前端缓存
# ============================================================================
if ($Cache) {
    Write-Host "[35m[前端缓存][0m"

    # node_modules/.cache
    Remove-ItemSafe -Path (Join-Path $FrontendDir "node_modules\.cache") -Description "npm 缓存"

    # .vite
    Remove-ItemSafe -Path (Join-Path $FrontendDir ".vite") -Description "Vite 缓存"

    # eslintcache
    Remove-ItemSafe -Path (Join-Path $FrontendDir ".eslintcache") -Description "ESLint 缓存"

    Write-Host ""
}

# ============================================================================
# 清理构建产物
# ============================================================================
if ($Build) {
    Write-Host "[35m[构建产物][0m"

    # 前端 dist
    Remove-ItemSafe -Path (Join-Path $FrontendDir "dist") -Description "前端构建 (dist)"

    # 前端 build
    Remove-ItemSafe -Path (Join-Path $FrontendDir "build") -Description "前端构建 (build)"

    # 后端 egg-info
    $eggDirs = Get-ChildItem -Path $BackendDir -Filter "*.egg-info" -Directory -ErrorAction SilentlyContinue
    foreach ($dir in $eggDirs) {
        Remove-ItemSafe -Path $dir.FullName -Description "egg-info: $($dir.Name)"
    }

    Write-Host ""
}

# ============================================================================
# 清理日志
# ============================================================================
if ($Logs) {
    Write-Host "[35m[日志文件][0m"

    if (Test-Path $LogsDir) {
        $logFiles = Get-ChildItem -Path $LogsDir -Filter "*.log" -File -ErrorAction SilentlyContinue
        foreach ($file in $logFiles) {
            Remove-ItemSafe -Path $file.FullName -Description "日志: $($file.Name)"
        }
    } else {
        Write-Status "SKIP" "日志目录不存在"
    }

    Write-Host ""
}

# ============================================================================
# 清理依赖（危险操作）
# ============================================================================
if ($Dependencies) {
    Write-Host "[35m[依赖目录][0m"
    Write-Host "[33m  警告: 这将删除所有已安装的依赖![0m"
    Write-Host ""

    if (-not $DryRun) {
        $confirm = Read-Host "  确认删除依赖? (输入 'yes' 继续)"
        if ($confirm -ne "yes") {
            Write-Status "SKIP" "操作已取消"
            Write-Host ""
            exit 0
        }
    }

    # Python venv
    Remove-ItemSafe -Path (Join-Path $BackendDir "venv") -Description "Python 虚拟环境 (venv)"

    # node_modules
    Remove-ItemSafe -Path (Join-Path $FrontendDir "node_modules") -Description "Node 依赖 (node_modules)"

    Write-Host ""
}

# ============================================================================
# 总结
# ============================================================================
Write-Host "[35m[清理总结][0m"
if ($DryRun) {
    Write-Host "  预计清理: $script:TotalItems 个项目"
    Write-Host "  预计释放: $(Format-Size $script:TotalSize)"
    Write-Host ""
    Write-Host "[33m  运行 .\clean.ps1 (不带 -DryRun) 执行清理[0m"
} else {
    Write-Host "  已清理: $script:TotalItems 个项目"
    Write-Host "  已释放: $(Format-Size $script:TotalSize)"
}
Write-Host ""
