<#
.SYNOPSIS
    QuantVision v2.0 数据库备份脚本

.DESCRIPTION
    备份 PostgreSQL 数据库到文件

.PARAMETER Restore
    恢复模式，从备份文件恢复

.PARAMETER File
    指定备份/恢复文件

.PARAMETER List
    列出所有备份

.PARAMETER Clean
    清理旧备份（保留最近 7 天）

.EXAMPLE
    .\backup-db.ps1                    # 创建备份
    .\backup-db.ps1 -List              # 列出备份
    .\backup-db.ps1 -Restore -File backup.sql
    .\backup-db.ps1 -Clean

.NOTES
    作者: QuantVision Team
    版本: 2.0.0
#>

[CmdletBinding()]
param(
    [switch]$Restore,
    [string]$File,
    [switch]$List,
    [switch]$Clean,
    [int]$RetentionDays = 7
)

$ErrorActionPreference = "Stop"
$script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$script:BackupDir = Join-Path $ProjectRoot "backups"

# 数据库配置
$script:DbHost = $env:DB_HOST ?? "localhost"
$script:DbPort = $env:DB_PORT ?? "5432"
$script:DbName = $env:DB_NAME ?? "quantvision"
$script:DbUser = $env:DB_USER ?? "quantvision"
$script:DbPassword = $env:DB_PASSWORD ?? "quantvision123"

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

function Ensure-BackupDir {
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
}

function Get-DockerContainerName {
    # 尝试找到 PostgreSQL 容器
    $containers = @(
        "quantvision-dev-postgres",
        "quantvision-postgres",
        "postgres"
    )
    foreach ($name in $containers) {
        $status = docker inspect --format='{{.State.Status}}' $name 2>&1
        if ($LASTEXITCODE -eq 0 -and $status -eq "running") {
            return $name
        }
    }
    return $null
}

# Banner
Write-Host ""
Write-Host "[35m╔══════════════════════════════════════════════════════════════╗[0m"
Write-Host "[35m║              QuantVision v2.0 - 数据库备份                   ║[0m"
Write-Host "[35m╚══════════════════════════════════════════════════════════════╝[0m"
Write-Host ""

# ============================================================================
# 列出备份
# ============================================================================
if ($List) {
    Ensure-BackupDir

    $backups = Get-ChildItem -Path $BackupDir -Filter "*.sql" | Sort-Object LastWriteTime -Descending

    if ($backups.Count -eq 0) {
        Write-Status "INFO" "没有找到备份文件"
    } else {
        Write-Host "备份文件列表:"
        Write-Host ""
        Write-Host "  [90m文件名                              大小        日期[0m"
        Write-Host "  [90m─────────────────────────────────────────────────────────[0m"
        foreach ($backup in $backups) {
            $size = "{0:N2} MB" -f ($backup.Length / 1MB)
            $date = $backup.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            Write-Host "  $($backup.Name.PadRight(35)) $($size.PadLeft(10)) $date"
        }
        Write-Host ""
        Write-Host "  共 $($backups.Count) 个备份文件"
    }
    exit 0
}

# ============================================================================
# 清理旧备份
# ============================================================================
if ($Clean) {
    Ensure-BackupDir

    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $oldBackups = Get-ChildItem -Path $BackupDir -Filter "*.sql" |
                  Where-Object { $_.LastWriteTime -lt $cutoffDate }

    if ($oldBackups.Count -eq 0) {
        Write-Status "INFO" "没有需要清理的旧备份"
    } else {
        Write-Status "WAIT" "清理 $($oldBackups.Count) 个旧备份..."
        foreach ($backup in $oldBackups) {
            Remove-Item $backup.FullName -Force
            Write-Host "    已删除: $($backup.Name)" -ForegroundColor Gray
        }
        Write-Status "OK" "清理完成"
    }
    exit 0
}

# ============================================================================
# 恢复数据库
# ============================================================================
if ($Restore) {
    if (-not $File) {
        Write-Status "FAIL" "请指定备份文件: -File <filename>"
        exit 1
    }

    $backupFile = if ([System.IO.Path]::IsPathRooted($File)) {
        $File
    } else {
        Join-Path $BackupDir $File
    }

    if (-not (Test-Path $backupFile)) {
        Write-Status "FAIL" "备份文件不存在: $backupFile"
        exit 1
    }

    Write-Host "[33m警告: 此操作将覆盖现有数据库内容![0m"
    $confirm = Read-Host "确认恢复? (输入 'yes' 继续)"

    if ($confirm -ne "yes") {
        Write-Status "INFO" "操作已取消"
        exit 0
    }

    $containerName = Get-DockerContainerName

    if ($containerName) {
        Write-Status "WAIT" "从 Docker 容器恢复..."
        # 复制文件到容器
        docker cp $backupFile "${containerName}:/tmp/restore.sql"
        # 执行恢复
        $env:PGPASSWORD = $DbPassword
        docker exec -e PGPASSWORD=$DbPassword $containerName psql -U $DbUser -d $DbName -f /tmp/restore.sql 2>&1 | Out-Null
        # 清理临时文件
        docker exec $containerName rm /tmp/restore.sql
    } else {
        Write-Status "WAIT" "从本地恢复..."
        $env:PGPASSWORD = $DbPassword
        psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $backupFile 2>&1 | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Status "OK" "数据库恢复完成: $([System.IO.Path]::GetFileName($backupFile))"
    } else {
        Write-Status "FAIL" "恢复失败"
    }
    exit 0
}

# ============================================================================
# 创建备份
# ============================================================================
Ensure-BackupDir

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFileName = "quantvision_${timestamp}.sql"
$backupFilePath = Join-Path $BackupDir $backupFileName

$containerName = Get-DockerContainerName

if ($containerName) {
    Write-Status "WAIT" "从 Docker 容器备份..."
    # 使用 pg_dump 导出
    $env:PGPASSWORD = $DbPassword
    docker exec -e PGPASSWORD=$DbPassword $containerName pg_dump -U $DbUser -d $DbName --clean --if-exists > $backupFilePath 2>&1
} else {
    Write-Status "WAIT" "从本地数据库备份..."
    $env:PGPASSWORD = $DbPassword
    pg_dump -h $DbHost -p $DbPort -U $DbUser -d $DbName --clean --if-exists > $backupFilePath 2>&1
}

if ($LASTEXITCODE -eq 0 -and (Test-Path $backupFilePath)) {
    $fileSize = "{0:N2} MB" -f ((Get-Item $backupFilePath).Length / 1MB)
    Write-Status "OK" "备份完成"
    Write-Host ""
    Write-Host "  文件: $backupFileName"
    Write-Host "  大小: $fileSize"
    Write-Host "  路径: $backupFilePath"
} else {
    Write-Status "FAIL" "备份失败"
    if (Test-Path $backupFilePath) {
        Remove-Item $backupFilePath -Force
    }
}

Write-Host ""
