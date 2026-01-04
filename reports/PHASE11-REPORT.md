# Phase 11: 数据层升级 - 实施报告

## 1. 概述

Phase 11 实现了完整的数据层升级，包括：
- **多数据源支持**：Polygon.io、Alpaca、IEX Cloud、Yahoo Finance
- **分钟级数据架构**：TimescaleDB 超表设计
- **日内因子引擎**：8 个实时计算的日内因子
- **数据 ETL 服务**：自动同步、缺失填充、质量检查

---

## 2. 技术架构

### 2.1 数据源架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据源层                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Polygon.io   │  │   Alpaca     │  │ IEX Cloud    │         │
│  │ (付费, 首选) │  │ (免费, 备用) │  │ (延迟15分)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           ▼                                     │
│                  ┌────────────────┐                            │
│                  │ DataSourceMgr  │  ← 自动故障转移            │
│                  └────────┬───────┘                            │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         ▼                 ▼                 ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Redis     │  │ TimescaleDB  │  │     S3       │         │
│  │ (实时,1小时) │  │ (分钟,1年)   │  │ (归档)       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
backend/
├── app/
│   ├── schemas/
│   │   └── market_data.py          # Pydantic 模型 (~350 行)
│   ├── models/
│   │   └── market_data.py          # SQLAlchemy 模型 (新增 ~330 行)
│   ├── services/
│   │   ├── data_source.py          # 数据源服务 (~450 行)
│   │   ├── data_etl.py             # ETL 服务 (~350 行)
│   │   └── intraday_factor_engine.py  # 日内因子 (~320 行)
│   └── api/v1/
│       └── market_data.py          # API 端点 (~250 行)

frontend/
├── src/
│   ├── types/
│   │   └── marketData.ts           # TypeScript 类型 (~350 行)
│   └── components/DataManagement/
│       ├── DataSourcePanel.tsx     # 数据源管理面板
│       └── index.ts
```

---

## 3. 数据源详情

### 3.1 支持的数据源

| 数据源 | 费用 | 实时 | 历史 | 分钟 | 优先级 |
|--------|------|:----:|:----:|:----:|:------:|
| Polygon.io | $200/月 | ✅ | ✅ | ✅ | 1 (首选) |
| Alpaca | 免费 | ✅ | ✅ | ✅ | 2 |
| IEX Cloud | $50/月 | ❌ | ✅ | ✅ | 3 |
| Yahoo Finance | 免费 | ❌ | ✅ | ❌ | 4 (备用) |

### 3.2 数据源接口

```python
class BaseDataSource(ABC):
    async def get_bars(symbol, frequency, start, end) -> list[OHLCVBar]
    async def get_quote(symbol) -> Quote
    async def get_snapshot(symbol) -> MarketSnapshot
```

### 3.3 故障转移机制

```python
# 自动按优先级尝试多个数据源
async def get_bars(symbol, ...):
    for source in [primary, alpaca, yahoo]:
        try:
            return await source.get_bars(...)
        except:
            continue  # 尝试下一个
    raise Exception("所有数据源失败")
```

---

## 4. 分钟级数据模型

### 4.1 TimescaleDB 超表

```sql
-- 分钟 K 线表
CREATE TABLE stock_minute_bar (
    symbol VARCHAR(20),
    timestamp TIMESTAMPTZ,
    frequency VARCHAR(10),
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    vwap FLOAT,
    PRIMARY KEY (symbol, timestamp, frequency)
);

-- 转换为 TimescaleDB 超表
SELECT create_hypertable('stock_minute_bar', 'timestamp',
       chunk_time_interval => interval '1 day');

-- 启用压缩
ALTER TABLE stock_minute_bar SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);
```

### 4.2 数据量估算

| 指标 | 值 |
|------|-----|
| 股票数量 | 4,000 |
| 每日分钟数 | 390 |
| 年交易日 | 252 |
| 每行字节 | ~100 |
| 年数据量 | ~2.4B 行, ~200GB |
| 日增量 | ~10M 行, ~1GB |

---

## 5. 日内因子

### 5.1 支持的日内因子

| 因子 ID | 名称 | 公式 | 解读 |
|---------|------|------|------|
| relative_volume | 相对成交量 | vol_10min / avg(vol_10min, 20) | >2.0 放量 |
| vwap_deviation | VWAP偏离 | (close - vwap) / vwap | >0 买压 |
| buy_pressure | 买卖压力 | buy_vol / total_vol | >0.6 买压强 |
| price_momentum_5min | 5分钟动量 | close / delay(close, 5) - 1 | 正值上涨 |
| price_momentum_15min | 15分钟动量 | close / delay(close, 15) - 1 | 正值上涨 |
| intraday_volatility | 日内波动 | std(returns) * sqrt(390*252) | 年化波动 |
| spread_ratio | 买卖价差比 | (ask-bid) / mid | 越大流动性越差 |
| order_imbalance | 订单不平衡 | (bid_size-ask_size) / total | >0 买盘强 |

### 5.2 因子计算示例

```python
async def calculate_factors(symbol, timestamp):
    bars = await get_intraday_bars(symbol, timestamp)

    factors = {
        'relative_volume': calc_relative_volume(bars),
        'vwap_deviation': calc_vwap_deviation(bars),
        'price_momentum_5min': calc_momentum(bars, 5),
        ...
    }

    return IntradayFactorSnapshot(
        symbol=symbol,
        timestamp=timestamp,
        factors=factors
    )
```

---

## 6. API 端点

### 6.1 数据源管理

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/market-data/sources` | 获取数据源列表 |
| POST | `/api/v1/market-data/sources/{source}/test` | 测试数据源连接 |

### 6.2 历史数据

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/market-data/historical` | 获取历史 K 线 |
| GET | `/api/v1/market-data/snapshot/{symbol}` | 获取市场快照 |
| POST | `/api/v1/market-data/snapshots` | 批量获取快照 |

### 6.3 数据同步

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/market-data/sync` | 同步历史数据 |
| GET | `/api/v1/market-data/sync/status` | 获取同步状态 |
| POST | `/api/v1/market-data/sync/fill-missing` | 填充缺失数据 |

### 6.4 日内因子

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/market-data/intraday-factors/definitions` | 因子定义 |
| GET | `/api/v1/market-data/intraday-factors/{symbol}` | 单股票因子 |
| POST | `/api/v1/market-data/intraday-factors/batch` | 批量计算 |

### 6.5 数据质量

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/market-data/quality/check` | 质量检查 |
| GET | `/api/v1/market-data/quality/report` | 质量报告 |
| POST | `/api/v1/market-data/quality/resolve/{id}` | 标记已解决 |

---

## 7. 数据质量检查

### 7.1 检测的问题类型

| 类型 | 严重度 | 描述 |
|------|:------:|------|
| missing_data | 中 | 缺失数据点 |
| invalid_ohlc | 高 | H<L 或 O/C 超出 H-L |
| zero_volume | 中 | 成交量为零 |
| price_gap | 中 | 价格跳空 >10% |
| outlier | 高 | 价格超过 5 倍标准差 |
| duplicate | 低 | 重复数据 |
| stale_data | 中 | 数据过期 |

### 7.2 质量评分

```python
score = 100 - (
    issues_low * 1 +
    issues_medium * 5 +
    issues_high * 10
)
```

---

## 8. 使用示例

### 8.1 同步历史数据

```typescript
// 同步 AAPL 一年的日线数据
const response = await fetch('/api/v1/market-data/sync', {
  method: 'POST',
  body: JSON.stringify(['AAPL', 'MSFT', 'GOOGL']),
  params: {
    start_date: '2024-01-01',
    end_date: '2025-01-01',
    frequency: '1day'
  }
})
```

### 8.2 获取日内因子

```typescript
// 获取实时日内因子
const factors = await fetch('/api/v1/market-data/intraday-factors/AAPL')
// { relative_volume: 1.8, vwap_deviation: 0.002, ... }
```

### 8.3 批量获取快照

```typescript
const snapshots = await fetch('/api/v1/market-data/snapshots', {
  method: 'POST',
  body: JSON.stringify(['AAPL', 'MSFT', 'GOOGL', 'AMZN'])
})
```

---

## 9. 配置

### 9.1 环境变量

```bash
# Polygon.io
POLYGON_API_KEY=your_polygon_key

# Alpaca
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret

# IEX Cloud
IEX_API_KEY=your_iex_key
```

### 9.2 数据源优先级

```python
# 默认优先级
1. Polygon (如果配置了 API key)
2. Alpaca (免费，推荐)
3. Yahoo (备用)
```

---

## 10. 总结

Phase 11 成功实现了：

- ✅ 多数据源支持 (Polygon, Alpaca, IEX, Yahoo)
- ✅ 自动故障转移机制
- ✅ TimescaleDB 分钟级数据模型
- ✅ 日内因子计算引擎 (8 个因子)
- ✅ 数据 ETL 服务 (同步、填充、检查)
- ✅ 数据质量监控
- ✅ 前端数据管理面板

**代码统计**：
- 后端新增：~1,700 行
- 前端新增：~550 行
- 总计：~2,250 行

**Phase 11 完成！**
