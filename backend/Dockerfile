# QuantVision Backend - Production Dockerfile
# Phase 3 Sprint 14: 生产部署准备
#
# 多阶段构建，优化镜像大小和安全性

# ==================== 构建阶段 ====================
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 使用 pip wheel 构建依赖
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==================== 生产阶段 ====================
FROM python:3.11-slim as production

WORKDIR /app

# 安装运行时依赖 + 创建用户
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 从构建阶段安装 wheels
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    PORT=8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health/live || exit 1

# 暴露端口
EXPOSE ${PORT}

# 启动命令 (使用 gunicorn 生产服务器)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 4 --loop uvloop --http httptools"]
