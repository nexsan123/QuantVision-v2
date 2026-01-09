# QuantVision Frontend - Production Dockerfile
# Phase 3 Sprint 14: 生产部署准备
#
# 多阶段构建，使用 Nginx 作为静态服务器

# ==================== 构建阶段 ====================
FROM node:20-alpine as builder

WORKDIR /app

# 安装依赖 (利用缓存)
COPY package*.json ./
RUN npm ci

# 复制源代码
COPY . .

# 构建参数
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_WS_URL=/ws
ARG VITE_ALPACA_ENV=paper

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_URL=$VITE_WS_URL \
    VITE_ALPACA_ENV=$VITE_ALPACA_ENV

# 构建应用
RUN npm run build

# ==================== 生产阶段 ====================
FROM nginx:alpine as production

# 安装 curl (健康检查)
RUN apk add --no-cache curl

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建非 root 用户运行
RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
