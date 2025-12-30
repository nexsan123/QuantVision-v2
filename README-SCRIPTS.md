# QuantVision v2.0 - 启动脚本使用指南

> 一键启动系统完整文档

---

## 目录结构

```
quantvision-v2/
├── start.ps1              # PowerShell 主启动脚本
├── stop.ps1               # 停止所有服务
├── start.bat              # CMD 快捷启动
├── stop.bat               # CMD 快捷停止
├── docker-compose.yml     # Docker 完整环境
├── docker-compose.dev.yml # Docker 开发环境（仅数据库）
├── .env.example           # 环境变量模板
├── .env                   # 环境变量（需从模板复制）
├── scripts/
│   ├── install.ps1        # 依赖安装脚本
│   ├── health-check.ps1   # 健康检查脚本
│   ├── backup-db.ps1      # 数据库备份
│   └── clean.ps1          # 清理缓存和临时文件
└── logs/                  # 日志目录
    ├── backend-*.log      # 后端日志（按日期）
    └── frontend-*.log     # 前端日志（按日期）
```

---

## 快速开始

### 首次使用

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
# 启动所有服务
.\start.ps1

# 或使用 CMD
start.bat

# 停止服务
.\stop.ps1
```

---

## 主启动脚本 (start.ps1)

### 功能特性

- ✅ 自动检查 Python (3.11+) 和 Node.js (18+)
- ✅ 自动创建/检测虚拟环境
- ✅ 自动安装缺失依赖
- ✅ 支持 Docker 数据库启动
- ✅ 彩色状态输出
- ✅ 健康检查
- ✅ 日志文件按日期滚动
- ✅ 自动打开浏览器

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-BackendOnly` | 只启动后端服务 | `.\start.ps1 -BackendOnly` |
| `-FrontendOnly` | 只启动前端服务 | `.\start.ps1 -FrontendOnly` |
| `-WithDocker` | 同时启动 Docker 数据库 | `.\start.ps1 -WithDocker` |
| `-Install` | 强制重新安装依赖 | `.\start.ps1 -Install` |
| `-NoBrowser` | 不自动打开浏览器 | `.\start.ps1 -NoBrowser` |
| `-Production` | 生产模式（构建后预览） | `.\start.ps1 -Production` |

### 使用示例

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
```

---

## 停止脚本 (stop.ps1)

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-All` | 停止全部（含 Docker） | `.\stop.ps1 -All` |
| `-Docker` | 只停止 Docker 容器 | `.\stop.ps1 -Docker` |
| `-Force` | 强制终止所有相关进程 | `.\stop.ps1 -Force` |

### 使用示例

```powershell
# 停止前后端服务
.\stop.ps1

# 停止所有服务（包括 Docker）
.\stop.ps1 -All

# 强制停止
.\stop.ps1 -Force
```

---

## Docker 环境

### 开发环境（仅数据库）

```bash
# 启动 PostgreSQL + Redis
docker-compose -f docker-compose.dev.yml up -d

# 停止
docker-compose -f docker-compose.dev.yml down

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 完整环境（生产）

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看特定服务日志
docker-compose logs -f backend
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | TimescaleDB 时序数据库 |
| Redis | 6379 | 缓存和消息队列 |
| Backend | 8000 | FastAPI 后端 |
| Frontend | 5173 | Vite 开发服务器 |
| Adminer | 8080 | 数据库管理界面（开发环境） |
| Redis Commander | 8081 | Redis 管理界面（开发环境） |
| Flower | 5555 | Celery 监控面板 |

---

## 辅助脚本

### 依赖安装 (scripts/install.ps1)

```powershell
# 安装所有依赖
.\scripts\install.ps1

# 只安装后端
.\scripts\install.ps1 -Backend

# 只安装前端
.\scripts\install.ps1 -Frontend

# 强制重新安装
.\scripts\install.ps1 -Force

# 初始化数据库
.\scripts\install.ps1 -InitDB
```

### 健康检查 (scripts/health-check.ps1)

```powershell
# 执行健康检查
.\scripts\health-check.ps1

# 输出 JSON 格式
.\scripts\health-check.ps1 -Json

# 持续监控模式（每 5 秒刷新）
.\scripts\health-check.ps1 -Watch

# 自定义监控间隔
.\scripts\health-check.ps1 -Watch -Interval 10
```

### 数据库备份 (scripts/backup-db.ps1)

```powershell
# 创建备份
.\scripts\backup-db.ps1

# 列出所有备份
.\scripts\backup-db.ps1 -List

# 从备份恢复
.\scripts\backup-db.ps1 -Restore -File backup_20250101.sql

# 清理旧备份（保留最近 7 天）
.\scripts\backup-db.ps1 -Clean

# 自定义保留天数
.\scripts\backup-db.ps1 -Clean -RetentionDays 14
```

### 清理工具 (scripts/clean.ps1)

```powershell
# 清理缓存和构建产物（默认）
.\scripts\clean.ps1

# 清理所有（包括依赖）
.\scripts\clean.ps1 -All

# 只清理缓存
.\scripts\clean.ps1 -Cache

# 只清理构建产物
.\scripts\clean.ps1 -Build

# 清理日志文件
.\scripts\clean.ps1 -Logs

# 清理依赖（危险！）
.\scripts\clean.ps1 -Dependencies

# 预览模式（不实际删除）
.\scripts\clean.ps1 -All -DryRun
```

---

## 环境变量配置 (.env)

### 必要配置

```env
# Alpaca API（美股数据/交易）
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key

# 数据库密码（生产环境请修改）
DB_PASSWORD=your_secure_password
```

### 可选配置

```env
# FRED API（宏观经济数据）
FRED_API_KEY=your_api_key

# Polygon API（备用数据源）
POLYGON_API_KEY=your_api_key

# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 应用环境
APP_ENV=development  # development, production
```

### 获取 API Key

| 服务 | 获取地址 | 用途 |
|------|---------|------|
| Alpaca | https://app.alpaca.markets/ | 美股数据和交易 |
| FRED | https://fred.stlouisfed.org/docs/api/api_key.html | 宏观经济数据 |
| Polygon | https://polygon.io/ | 备用行情数据 |

---

## 常见问题

### Q: PowerShell 执行策略错误

```
无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本。
```

**解决方案：**

```powershell
# 方法 1：临时绕过（推荐）
powershell -ExecutionPolicy Bypass -File .\start.ps1

# 方法 2：修改执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 端口被占用

```
端口 8000 被占用
```

**解决方案：**

```powershell
# 查看占用进程
netstat -ano | findstr :8000

# 强制停止
.\stop.ps1 -Force
```

### Q: Docker 容器无法启动

```
Cannot connect to the Docker daemon
```

**解决方案：**
1. 启动 Docker Desktop
2. 等待 Docker 完全启动（托盘图标变绿）
3. 重新运行启动脚本

### Q: Python 虚拟环境问题

```
无法激活虚拟环境
```

**解决方案：**

```powershell
# 删除现有环境
.\scripts\clean.ps1 -Dependencies

# 重新安装
.\scripts\install.ps1 -Force
```

### Q: 前端依赖安装失败

```
npm ERR! code ERESOLVE
```

**解决方案：**

```powershell
# 清理 node_modules
.\scripts\clean.ps1 -Dependencies

# 使用 legacy peer deps
cd frontend
npm install --legacy-peer-deps
```

### Q: 数据库连接失败

```
Connection refused: localhost:5432
```

**解决方案：**

```powershell
# 启动 Docker 数据库
docker-compose -f docker-compose.dev.yml up -d postgres

# 检查状态
.\scripts\health-check.ps1
```

### Q: 中文乱码

**解决方案：**
1. 确保 PowerShell 使用 UTF-8：
   ```powershell
   chcp 65001
   ```
2. 或使用 Windows Terminal

---

## 日志文件

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

## 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:5173 | React 应用 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | ReDoc 文档 |
| WebSocket | ws://localhost:8000/ws/trading | 交易事件流 |
| 健康检查 | http://localhost:8000/api/v1/health | 服务状态 |

---

## 更新日志

### v2.0.0 (2025-12-29)

- 新增一键启动系统
- 支持多参数组合
- 彩色状态输出
- 日志按日期滚动
- Docker Compose 配置
- 完整辅助脚本套件

---

## 技术支持

如遇到问题，请：

1. 运行健康检查：`.\scripts\health-check.ps1`
2. 查看日志文件：`.\logs\`
3. 检查环境变量：`.env`
4. 提交 Issue：https://github.com/your-repo/quantvision/issues

---

**QuantVision v2.0** - 量化投资平台
