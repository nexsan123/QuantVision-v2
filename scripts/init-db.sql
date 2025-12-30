-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║                     QuantVision v2.0 - 数据库初始化                         ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
--
-- 此脚本在 PostgreSQL 容器首次启动时自动执行
-- 用于创建扩展和初始配置
--

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用 pg_trgm 扩展（用于模糊搜索）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 创建索引优化设置
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- 输出确认信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'QuantVision 数据库初始化完成';
    RAISE NOTICE '========================================';
END
$$;
