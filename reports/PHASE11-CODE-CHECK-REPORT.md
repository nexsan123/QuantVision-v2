# Phase 11: 数据层升级 - 代码检查报告

## 1. 新增文件清单

### 后端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `backend/app/schemas/market_data.py` | ~350 | Pydantic 市场数据模型 |
| `backend/app/services/data_source.py` | ~450 | 多数据源服务 |
| `backend/app/services/data_etl.py` | ~350 | 数据 ETL 服务 |
| `backend/app/services/intraday_factor_engine.py` | ~320 | 日内因子引擎 |
| `backend/app/api/v1/market_data.py` | ~250 | 市场数据 API |

### 后端修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `backend/app/models/market_data.py` | 新增 StockMinuteBar, IntradayFactor, DataSyncLog, DataQualityIssue 模型 |
| `backend/app/api/v1/__init__.py` | 添加 market_data 模块导出 |
| `backend/app/main.py` | 注册 market_data 路由 |

### 前端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `frontend/src/types/marketData.ts` | ~350 | TypeScript 类型定义 |
| `frontend/src/components/DataManagement/DataSourcePanel.tsx` | ~200 | 数据源管理面板 |
| `frontend/src/components/DataManagement/index.ts` | ~5 | 组件导出 |

## 2. 数据模型检查

### 2.1 新增 SQLAlchemy 模型

```python
# StockMinuteBar - 分钟 K 线
class StockMinuteBar(Base):
    symbol: str  # PK
    timestamp: datetime  # PK
    frequency: str  # PK
    open, high, low, close: float
    volume: int
    vwap, day_open, day_high, day_low: float | None
    day_volume: int | None
    pre_market, after_hours: bool
    source: str

# IntradayFactor - 日内因子
class IntradayFactor(Base):
    symbol: str  # PK
    timestamp: datetime  # PK
    factor_id: str  # PK
    value: float
    zscore, percentile: float | None

# DataSyncLog - 同步日志
class DataSyncLog(Base, UUIDMixin, TimestampMixin):
    symbol, frequency, data_source: str
    start_date, end_date: datetime
    status: str  # pending, syncing, completed, failed
    bars_synced: int
    error_message: str | None

# DataQualityIssue - 数据质量问题
class DataQualityIssue(Base, UUIDMixin, TimestampMixin):
    symbol: str
    issue_timestamp: datetime
    issue_type, severity, description: str
    resolved: bool
```

### 2.2 Pydantic Schema

```python
# 枚举类型
class DataSource(str, Enum): POLYGON, ALPACA, IEX, YAHOO
class DataFrequency(str, Enum): MIN_1, MIN_5, ..., DAY_1
class DataSyncStatus(str, Enum): SYNCED, SYNCING, ERROR, STALE
class IntradayFactorType(str, Enum): RELATIVE_VOLUME, VWAP_DEVIATION, ...

# 数据模型
class OHLCVBar(BaseModel): symbol, timestamp, ohlcv, vwap, trades
class MinuteBar(OHLCVBar): frequency, pre_market, after_hours, day_*
class MarketSnapshot(BaseModel): symbol, last_price, change, ohlcv, bid/ask
```

## 3. API 端点检查

### 3.1 端点列表

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/market-data/sources` | 数据源列表 |
| POST | `/api/v1/market-data/sources/{source}/test` | 测试连接 |
| POST | `/api/v1/market-data/historical` | 历史数据 |
| GET | `/api/v1/market-data/snapshot/{symbol}` | 市场快照 |
| POST | `/api/v1/market-data/snapshots` | 批量快照 |
| POST | `/api/v1/market-data/sync` | 同步数据 |
| GET | `/api/v1/market-data/sync/status` | 同步状态 |
| POST | `/api/v1/market-data/sync/fill-missing` | 填充缺失 |
| GET | `/api/v1/market-data/intraday-factors/definitions` | 因子定义 |
| GET | `/api/v1/market-data/intraday-factors/{symbol}` | 单股票因子 |
| POST | `/api/v1/market-data/intraday-factors/batch` | 批量因子 |
| GET | `/api/v1/market-data/intraday-factors/latest` | 最新因子 |
| POST | `/api/v1/market-data/quality/check` | 质量检查 |
| GET | `/api/v1/market-data/quality/report` | 质量报告 |
| POST | `/api/v1/market-data/quality/resolve/{id}` | 标记解决 |

### 3.2 路由注册确认

```python
# main.py
from app.api.v1 import ..., market_data, ...

app.include_router(
    market_data.router,
    prefix=settings.API_V1_PREFIX,
    tags=["市场数据"],
)
```

## 4. 服务层检查

### 4.1 DataSourceManager

```python
class DataSourceManager:
    _sources: dict[DataSource, BaseDataSource]
    _primary_source: DataSource

    async def initialize()  # 初始化数据源
    async def shutdown()    # 关闭连接
    def get_source(source)  # 获取数据源
    async def get_bars(...)  # 获取 K 线 (自动故障转移)
    async def get_snapshot(symbol)  # 获取快照
```

### 4.2 数据源实现

```python
class PolygonDataSource(BaseDataSource):
    base_url = "https://api.polygon.io"
    rate_limit = 100  # /分钟

class AlpacaDataSource(BaseDataSource):
    base_url = "https://data.alpaca.markets"
    rate_limit = 200

class YahooDataSource(BaseDataSource):
    # 使用 yfinance 库
```

### 4.3 ETL 服务

```python
class DataETLService:
    async def sync_historical_data(symbols, frequency, start, end)
    async def get_sync_status(symbols, frequency)
    async def fill_missing_data(symbol, frequency, start, end)
    async def check_data_quality(symbols, frequency, start, end)
```

### 4.4 日内因子引擎

```python
class IntradayFactorEngine:
    async def calculate_factors(symbol, timestamp) -> IntradayFactorSnapshot
    async def calculate_batch(symbols, timestamp) -> list[IntradayFactorSnapshot]
    async def save_factors(snapshots) -> int
    async def get_factor_history(symbol, factor_id, start, end)

    # 因子计算
    def _calc_relative_volume(df)
    def _calc_vwap_deviation(df)
    def _calc_price_momentum(df, minutes)
    def _calc_intraday_volatility(df)
```

## 5. 依赖检查

### 5.1 后端依赖

```python
# data_source.py
import httpx
import structlog
import yfinance as yf  # Yahoo Finance

# data_etl.py
import pandas as pd
import numpy as np
from sqlalchemy.dialects.postgresql import insert

# intraday_factor_engine.py
import numpy as np
import pandas as pd
```

### 5.2 前端依赖

```typescript
// DataSourcePanel.tsx
import { Row, Col, Table, Tag, Button, Progress, ... } from 'antd'
import { Card } from '@/components/ui'
import { DataSource, DataSourceStatus, ... } from '@/types/marketData'
```

## 6. 编码规范检查

### 6.1 中文字符编码

所有中文使用 Unicode 转义序列：
```typescript
'\u6570\u636e\u6e90\u72b6\u6001'  // 数据源状态
'\u540c\u6b65\u5b8c\u6210'        // 同步完成
```

### 6.2 类型安全

- 后端：Pydantic 模型验证
- 前端：TypeScript 严格类型
- 数据库：SQLAlchemy 类型映射

## 7. 功能完整性检查

| 功能 | 状态 | 说明 |
|------|------|------|
| 多数据源支持 | ✅ | 4 个数据源 |
| 故障转移 | ✅ | 自动按优先级切换 |
| 分钟数据模型 | ✅ | TimescaleDB 超表设计 |
| 日内因子 | ✅ | 8 个因子 |
| 数据同步 | ✅ | 历史/增量同步 |
| 缺失填充 | ✅ | 自动检测填充 |
| 质量检查 | ✅ | 7 种问题类型 |
| API 端点 | ✅ | 15 个端点 |
| 前端组件 | ✅ | 数据源管理面板 |

## 8. 待优化项

1. **Redis 缓存**：添加实时数据 Redis 缓存层
2. **WebSocket 推送**：实时行情推送
3. **定时任务**：自动化数据同步调度
4. **压缩策略**：TimescaleDB 数据压缩配置
5. **监控告警**：数据延迟/缺失告警

## 9. 总结

Phase 11 代码检查通过：
- ✅ 文件结构完整
- ✅ 数据模型一致
- ✅ API 端点注册正确
- ✅ 服务层设计合理
- ✅ 依赖正确
- ✅ 编码规范符合要求
- ✅ 功能完整

**Phase 11 代码检查完成！**
