# QuantVision v2.0 一键启动系统 - 详细报告

> 生成日期: 2025-12-29

---

## 一、文件清单总览

| 文件 | 行数 | 用途 |
|------|------|------|
| `start.ps1` | 553 | PowerShell 主启动脚本 |
| `stop.ps1` | 218 | 停止所有服务 |
| `start.bat` | 25 | CMD 快捷启动 |
| `stop.bat` | 22 | CMD 快捷停止 |
| `docker-compose.yml` | 211 | Docker 完整环境 |
| `docker-compose.dev.yml` | 112 | Docker 开发环境（仅数据库） |
| `.env.example` | 70 | 环境变量模板 |
| `scripts/install.ps1` | 227 | 依赖安装脚本 |
| `scripts/health-check.ps1` | 275 | 健康检查脚本 |
| `scripts/backup-db.ps1` | 231 | 数据库备份工具 |
| `scripts/clean.ps1` | 261 | 清理缓存和临时文件 |
| `scripts/kill-ports.ps1` | 12 | 端口清理工具 |
| `scripts/init-db.sql` | 32 | 数据库初始化脚本 |
| `README-SCRIPTS.md` | 467 | 使用文档 |

**总计: 14 个文件, 2716 行代码**

---

## 二、核心脚本详解

### 2.1 主启动脚本 (start.ps1)

**支持参数:**

| 参数 | 说明 | 示例 |
|------|------|------|
| `-BackendOnly` | 只启动后端服务 | `.\start.ps1 -BackendOnly` |
| `-FrontendOnly` | 只启动前端服务 | `.\start.ps1 -FrontendOnly` |
| `-WithDocker` | 同时启动 Docker 数据库 | `.\start.ps1 -WithDocker` |
| `-Install` | 强制重新安装依赖 | `.\start.ps1 -Install` |
| `-NoBrowser` | 不自动打开浏览器 | `.\start.ps1 -NoBrowser` |
| `-Production` | 生产模式（构建后预览） | `.\start.ps1 -Production` |

**功能流程:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. 显示 ASCII Banner                                       │
│  2. 环境检查 (Python 3.11+, Node.js 18+, npm)              │
│  3. 依赖检查/安装 (venv, requirements.txt, node_modules)   │
│  4. Docker 服务启动 (可选)                                  │
│  5. 启动后端 (uvicorn --reload)                            │
│  6. 启动前端 (npm run dev / build + preview)               │
│  7. 健康检查 (API, DB, Redis)                              │
│  8. 显示服务地址，自动打开浏览器                            │
└─────────────────────────────────────────────────────────────┘
```

**关键技术细节:**

- 使用 `Write-Host -ForegroundColor` 实现彩色输出
- 使用 `cmd.exe /c "... > logfile 2>&1"` 合并日志输出
- 自动检测端口占用并释放
- 日志按日期滚动 (`logs/backend-yyyy-MM-dd.log`)

**核心函数:**

| 函数 | 用途 |
|------|------|
| `Show-Banner` | 显示 ASCII 艺术字 Banner |
| `Write-Status` | 彩色状态输出 (OK/FAIL/WAIT/INFO) |
| `Test-Environment` | 检查 Python/Node.js/Docker |
| `Test-Dependencies` | 检查/安装依赖 |
| `Start-DockerServices` | 启动 Docker 容器 |
| `Start-Backend` | 启动后端服务 |
| `Start-Frontend` | 启动前端服务 |
| `Test-Health` | 健康检查 |
| `Stop-ProcessOnPort` | 释放占用端口 |
| `Wait-ForService` | 等待服务就绪 |

---

### 2.2 停止脚本 (stop.ps1)

**支持参数:**

| 参数 | 说明 | 示例 |
|------|------|------|
| `-All` | 停止全部（含 Docker） | `.\stop.ps1 -All` |
| `-Docker` | 只停止 Docker 容器 | `.\stop.ps1 -Docker` |
| `-Force` | 强制终止所有相关进程 | `.\stop.ps1 -Force` |

**停止策略:**

1. 按端口停止 (`Get-NetTCPConnection`)
2. 按进程名停止 (python*, node*)
3. 按命令行匹配 (uvicorn, vite, quantvision)

**核心函数:**

| 函数 | 用途 |
|------|------|
| `Stop-ProcessOnPort` | 按端口停止进程 |
| `Stop-BackendService` | 停止后端服务 |
| `Stop-FrontendService` | 停止前端服务 |
| `Stop-DockerServices` | 停止 Docker 容器 |
| `Stop-AllForce` | 强制停止所有相关进程 |

---

## 三、Docker 配置

### 3.1 开发环境 (docker-compose.dev.yml)

**服务列表:**

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | timescale/timescaledb:latest-pg15 | 5432 | TimescaleDB 时序数据库 |
| redis | redis:7-alpine | 6379 | 缓存和消息队列 |
| adminer | adminer:latest | 8080 | 数据库管理界面 |
| redis-commander | rediscommander/redis-commander | 8081 | Redis 管理界面 |

**数据持久化:**

```yaml
volumes:
  quantvision-dev-postgres-data:  # PostgreSQL 数据
  quantvision-dev-redis-data:     # Redis 数据
```

**特性:**

- TimescaleDB 扩展预装
- 健康检查配置
- 自动重启策略 (`restart: unless-stopped`)
- 初始化脚本挂载 (`scripts/init-db.sql`)

---

### 3.2 完整环境 (docker-compose.yml)

**服务列表:**

| 服务 | 端口 | 说明 |
|------|------|------|
| postgres | 5432 | TimescaleDB 数据库 |
| redis | 6379 | 缓存服务 |
| backend | 8000 | FastAPI 后端 |
| frontend | 5173/80 | React 前端 |
| celery-worker | - | Celery 异步任务 |
| celery-beat | - | Celery 定时任务 |
| flower | 5555 | Celery 监控面板 |

**服务依赖关系:**

```
postgres ─┬─> backend ─┬─> celery-worker
redis ────┤            ├─> celery-beat
          │            └─> flower
          └─> frontend
```

---

## 四、辅助脚本

### 4.1 安装脚本 (scripts/install.ps1)

**参数:**

| 参数 | 说明 |
|------|------|
| `-Backend` | 只安装后端依赖 |
| `-Frontend` | 只安装前端依赖 |
| `-InitDB` | 初始化数据库（运行 migrations） |
| `-Force` | 强制重新安装（删除现有环境） |

**安装流程:**

```
1. 创建/更新 Python 虚拟环境 (venv)
2. 安装 requirements.txt 依赖
3. 安装 node_modules 依赖
4. 运行数据库迁移 (alembic upgrade head)
```

---

### 4.2 健康检查 (scripts/health-check.ps1)

**参数:**

| 参数 | 说明 |
|------|------|
| `-Json` | 输出 JSON 格式 |
| `-Watch` | 持续监控模式 |
| `-Interval` | 监控间隔（秒，默认 5） |

**检查项目:**

| 检查项 | 方法 |
|--------|------|
| Backend API | HTTP GET /api/v1/health |
| Database | pg_isready / TCP 5432 |
| Redis | redis-cli ping / TCP 6379 |
| 端口状态 | Get-NetTCPConnection |
| 进程状态 | Get-Process |

**输出示例:**

```
╔══════════════════════════════════════════════════════════════╗
║                    QuantVision Health Check                  ║
╠══════════════════════════════════════════════════════════════╣
║  Backend API:     ● Healthy                                  ║
║  Database:        ● Connected                                ║
║  Redis:           ● Connected                                ║
║  Port 8000:       ● In Use (python.exe)                     ║
║  Port 5173:       ● In Use (node.exe)                       ║
╠══════════════════════════════════════════════════════════════╣
║  Overall Status:  ✓ All Systems Operational                 ║
╚══════════════════════════════════════════════════════════════╝
```

---

### 4.3 数据库备份 (scripts/backup-db.ps1)

**参数:**

| 参数 | 说明 |
|------|------|
| `-Restore` | 恢复模式 |
| `-File <name>` | 指定备份文件 |
| `-List` | 列出所有备份 |
| `-Clean` | 清理旧备份 |
| `-RetentionDays` | 保留天数（默认 7） |

**备份文件:**

- 位置: `backups/backup_yyyyMMdd_HHmmss.sql`
- 格式: pg_dump 自定义格式
- 压缩: 自动压缩

**使用示例:**

```powershell
# 创建备份
.\scripts\backup-db.ps1

# 列出备份
.\scripts\backup-db.ps1 -List

# 恢复备份
.\scripts\backup-db.ps1 -Restore -File backup_20250101_120000.sql

# 清理 7 天前的备份
.\scripts\backup-db.ps1 -Clean -RetentionDays 7
```

---

### 4.4 清理工具 (scripts/clean.ps1)

**参数:**

| 参数 | 说明 |
|------|------|
| `-All` | 清理全部 |
| `-Cache` | 只清理缓存 |
| `-Build` | 只清理构建产物 |
| `-Logs` | 清理日志文件 |
| `-Dependencies` | 清理依赖（危险！） |
| `-DryRun` | 预览模式（不实际删除） |

**清理目标:**

| 类别 | 目标 |
|------|------|
| Cache | `__pycache__`, `.pytest_cache`, `.mypy_cache` |
| Build | `dist`, `build`, `.next`, `.vite` |
| Logs | `logs/*.log` |
| Dependencies | `venv`, `node_modules` |

---

### 4.5 端口清理 (scripts/kill-ports.ps1)

**功能:** 强制终止占用 8000 和 5173 端口的进程

```powershell
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        Write-Host "Killing process $processId on port $port"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}
```

---

## 五、环境变量配置 (.env.example)

### 必填配置

```env
# Alpaca API（美股数据/交易）
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### 数据库配置

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantvision
DB_USER=quantvision
DB_PASSWORD=quantvision123
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

### Redis 配置

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}
```

### 可选配置

```env
# FRED API（宏观经济数据）
FRED_API_KEY=

# Polygon API（备用数据源）
POLYGON_API_KEY=

# 应用配置
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 安全配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# 性能配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
RATE_LIMIT_PER_MINUTE=100
```

### API Key 获取地址

| 服务 | 获取地址 | 用途 |
|------|---------|------|
| Alpaca | https://app.alpaca.markets/ | 美股数据和交易 |
| FRED | https://fred.stlouisfed.org/docs/api/api_key.html | 宏观经济数据 |
| Polygon | https://polygon.io/ | 备用行情数据 |

---

## 六、数据库初始化 (scripts/init-db.sql)

**启用扩展:**

```sql
-- TimescaleDB 时序数据扩展
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- UUID 生成扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 模糊搜索扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**性能优化:**

```sql
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
```

---

## 七、使用示例

### 首次启动

```powershell
# 1. 进入项目目录
cd F:\量化交易\quantvision-v2

# 2. 复制环境变量模板
cp .env.example .env

# 3. 编辑 .env 文件，配置 API 密钥
notepad .env

# 4. 安装依赖
.\scripts\install.ps1

# 5. 启动服务
.\start.ps1
```

### 日常使用

```powershell
# 标准启动（开发模式）
.\start.ps1

# 启动后端 + Docker 数据库
.\start.ps1 -BackendOnly -WithDocker

# 重新安装依赖后启动
.\start.ps1 -Install

# 生产模式预览
.\start.ps1 -Production

# 不打开浏览器
.\start.ps1 -NoBrowser

# 停止服务
.\stop.ps1

# 停止所有服务（包括 Docker）
.\stop.ps1 -All

# 强制停止
.\stop.ps1 -Force
```

### 维护操作

```powershell
# 健康检查
.\scripts\health-check.ps1

# 持续监控
.\scripts\health-check.ps1 -Watch

# 备份数据库
.\scripts\backup-db.ps1

# 列出备份
.\scripts\backup-db.ps1 -List

# 恢复备份
.\scripts\backup-db.ps1 -Restore -File backup_20250101.sql

# 清理缓存（预览）
.\scripts\clean.ps1 -All -DryRun

# 实际清理
.\scripts\clean.ps1 -Cache -Build
```

### CMD 快捷方式

```batch
:: 双击 start.bat 启动
start.bat

:: 双击 stop.bat 停止
stop.bat
```

---

## 八、已修复的问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| ANSI 转义码解析错误 | PowerShell 解释 `[32m` 为类型转换 | 改用 `Write-Host -ForegroundColor` |
| 日志重定向失败 | `RedirectStandardOutput` 和 `RedirectStandardError` 不能相同 | 使用 `cmd.exe /c "... > file 2>&1"` |
| `$pid` 只读错误 | PowerShell 保留变量 | 重命名为 `$processId` |
| 端口冲突 | 多进程占用同一端口 | 添加 `Stop-ProcessOnPort` 函数 |

---

## 九、服务端口汇总

| 服务 | 端口 | URL | 说明 |
|------|------|-----|------|
| Frontend | 5173 | http://localhost:5173 | React 应用 |
| Backend API | 8000 | http://localhost:8000 | FastAPI 服务 |
| API Docs | 8000 | http://localhost:8000/docs | Swagger UI |
| ReDoc | 8000 | http://localhost:8000/redoc | ReDoc 文档 |
| WebSocket | 8000 | ws://localhost:8000/ws/trading | 交易事件流 |
| Health Check | 8000 | http://localhost:8000/api/v1/health | 健康检查 |
| PostgreSQL | 5432 | - | TimescaleDB |
| Redis | 6379 | - | 缓存服务 |
| Adminer | 8080 | http://localhost:8080 | DB 管理 |
| Redis Commander | 8081 | http://localhost:8081 | Redis 管理 |
| Flower | 5555 | http://localhost:5555 | Celery 监控 |

---

## 十、测试结果

**测试时间:** 2025-12-29

**环境检查:**

```
[Environment Check]
  [OK] Python 3.14.2 installed
  [OK] Node.js v24.9.0 installed
  [OK] npm 11.6.0 installed
  [i] Docker available (use -WithDocker to start database)
```

**依赖检查:**

```
[Dependencies Check]
  [OK] Backend virtual environment created
  [OK] Backend dependencies installed
  [OK] Frontend dependencies ready (node_modules)
  [i] Created .env from .env.example
```

**服务启动:**

```
[Starting Services]
  [OK] Backend service started (PID: xxx)
  [OK] Frontend service started (PID: xxx)
```

**健康检查:**

```
[Health Check]
  [INFO] Backend API status: degraded  # 预期（无 DB/Redis）
```

**验证命令:**

```powershell
curl http://localhost:8000/api/v1/health
# 返回: {"status":"degraded",...}  ✓
```

---

## 十一、常见问题

### Q: PowerShell 执行策略错误

```
无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本。
```

**解决方案:**

```powershell
# 方法 1：临时绕过（推荐）
powershell -ExecutionPolicy Bypass -File .\start.ps1

# 方法 2：修改执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 端口被占用

```powershell
# 查看占用进程
netstat -ano | findstr :8000

# 强制停止
.\stop.ps1 -Force

# 或使用端口清理脚本
.\scripts\kill-ports.ps1
```

### Q: Docker 容器无法启动

1. 启动 Docker Desktop
2. 等待 Docker 完全启动（托盘图标变绿）
3. 重新运行启动脚本

### Q: Python 虚拟环境问题

```powershell
# 删除现有环境
.\scripts\clean.ps1 -Dependencies

# 重新安装
.\scripts\install.ps1 -Force
```

### Q: 前端依赖安装失败

```powershell
# 清理 node_modules
.\scripts\clean.ps1 -Dependencies

# 使用 legacy peer deps
cd frontend
npm install --legacy-peer-deps
```

### Q: 数据库连接失败

```powershell
# 启动 Docker 数据库
docker-compose -f docker-compose.dev.yml up -d postgres

# 检查状态
.\scripts\health-check.ps1
```

### Q: 中文乱码

```powershell
# 设置 PowerShell 为 UTF-8
chcp 65001

# 或使用 Windows Terminal
```

---

## 十二、日志文件

### 位置

```
logs/
├── backend-2025-01-01.log   # 后端日志
├── frontend-2025-01-01.log  # 前端日志
└── ...
```

### 查看日志

```powershell
# 实时查看后端日志
Get-Content .\logs\backend-*.log -Wait -Tail 50

# 搜索错误
Select-String -Path .\logs\*.log -Pattern "ERROR"
```

---

## 十三、版本信息

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.11 |
| Node.js | >= 18.0 |
| Docker | 可选 |
| PostgreSQL | 15 (TimescaleDB) |
| Redis | 7 |

---

## 十四、更新日志

### v2.0.0 (2025-12-29)

- 新增一键启动系统
- 支持多参数组合
- 彩色状态输出
- 日志按日期滚动
- Docker Compose 配置
- 完整辅助脚本套件
- 修复 ANSI 转义码问题
- 修复日志重定向问题
- 修复端口冲突问题

---

**QuantVision v2.0** - 量化投资平台
