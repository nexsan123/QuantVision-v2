# Phase 12: 执行层升级 - 代码检查报告

## 1. 新增文件清单

### 后端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `backend/app/schemas/trading.py` | ~350 | Pydantic 交易模型 |
| `backend/app/services/broker_service.py` | ~550 | 券商服务 |
| `backend/app/services/slippage_model.py` | ~450 | 滑点模型 |
| `backend/app/api/v1/trading.py` | ~350 | 交易 API |

### 后端修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `backend/app/api/v1/__init__.py` | 添加 trading 模块导出 |
| `backend/app/main.py` | 注册 trading 路由 |

### 前端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `frontend/src/types/trading.ts` | ~460 | TypeScript 类型定义 (扩展) |
| `frontend/src/components/TradingCenter/BrokerPanel.tsx` | ~200 | 券商连接面板 |
| `frontend/src/components/TradingCenter/OrderPanel.tsx` | ~350 | 订单面板 |
| `frontend/src/components/TradingCenter/PositionsTable.tsx` | ~200 | 持仓表格 |
| `frontend/src/components/TradingCenter/index.ts` | ~10 | 组件导出 |

## 2. 数据模型检查

### 2.1 Pydantic Schema

```python
# 枚举类型
class BrokerType(str, Enum): ALPACA, INTERACTIVE_BROKERS, PAPER
class BrokerConnectionStatus(str, Enum): DISCONNECTED, CONNECTING, CONNECTED, ERROR
class OrderSide(str, Enum): BUY, SELL
class OrderType(str, Enum): MARKET, LIMIT, STOP, STOP_LIMIT
class OrderStatus(str, Enum): PENDING, SUBMITTED, ACCEPTED, PARTIAL, FILLED, CANCELLED
class SlippageModelType(str, Enum): FIXED, VOLUME_BASED, SQRT, ALMGREN_CHRISS
class ExecutionAlgorithm(str, Enum): MARKET, TWAP, VWAP, POV, IS

# 数据模型
class BrokerAccount(BaseModel): id, broker, account_number, equity, cash, buying_power, ...
class BrokerPosition(BaseModel): symbol, quantity, side, avg_entry_price, unrealized_pnl, ...
class CreateOrderRequest(BaseModel): symbol, side, quantity, order_type, limit_price, ...
class OrderResponse(BaseModel): id, symbol, status, filled_quantity, filled_avg_price, ...
class AlmgrenChrissParams(BaseModel): eta, gamma, sigma, spread_bps
class SlippageResult(BaseModel): total_slippage, fixed_cost, temporary_impact, permanent_impact
```

### 2.2 TypeScript 类型

```typescript
// 券商类型
type BrokerType = 'alpaca' | 'interactive_brokers' | 'paper'
interface BrokerAccount { id, broker, equity, cash, buyingPower, ... }
interface BrokerPosition { symbol, quantity, side, avgEntryPrice, unrealizedPnl, ... }

// 滑点模型
type SlippageModelType = 'fixed' | 'volume_based' | 'sqrt' | 'almgren_chriss'
interface AlmgrenChrissParams { eta, gamma, sigma, spreadBps }
interface SlippageResult { totalSlippage, fixedCost, temporaryImpact, permanentImpact }

// 订单类型
interface CreateOrderRequest { symbol, side, quantity, orderType, limitPrice, ... }
interface OrderResponse { id, symbol, status, filledQuantity, filledAvgPrice, ... }
```

## 3. API 端点检查

### 3.1 端点列表

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/trading/brokers` | 券商列表 |
| GET | `/api/v1/trading/status` | 交易状态 |
| POST | `/api/v1/trading/connect/{broker}` | 连接券商 |
| GET | `/api/v1/trading/account` | 账户信息 |
| GET | `/api/v1/trading/positions` | 持仓查询 |
| POST | `/api/v1/trading/orders` | 提交订单 |
| GET | `/api/v1/trading/orders` | 订单列表 |
| GET | `/api/v1/trading/orders/{id}` | 订单详情 |
| DELETE | `/api/v1/trading/orders/{id}` | 取消订单 |
| GET | `/api/v1/trading/slippage/models` | 滑点模型 |
| POST | `/api/v1/trading/slippage/estimate` | 滑点估算 |
| POST | `/api/v1/trading/slippage/batch` | 批量估算 |
| POST | `/api/v1/trading/paper/enable` | 启用模拟盘 |
| POST | `/api/v1/trading/paper/disable` | 禁用模拟盘 |
| GET | `/api/v1/trading/paper/state` | 模拟盘状态 |
| GET | `/api/v1/trading/stats` | 交易统计 |

### 3.2 路由注册确认

```python
# main.py
from app.api.v1 import ..., trading, ...

app.include_router(
    trading.router,
    prefix=settings.API_V1_PREFIX,
    tags=["交易"],
)
```

## 4. 服务层检查

### 4.1 BrokerManager

```python
class BrokerManager:
    _brokers: dict[BrokerType, BaseBroker]
    _primary_broker: BrokerType | None

    async def initialize()           # 初始化券商
    async def shutdown()             # 关闭连接
    def get_broker(broker_type)      # 获取券商
    async def switch_broker(type)    # 切换券商
    def get_available_brokers()      # 可用券商列表
```

### 4.2 券商实现

```python
class AlpacaBroker(BaseBroker):
    LIVE_BASE_URL = "https://api.alpaca.markets"
    PAPER_BASE_URL = "https://paper-api.alpaca.markets"

    async def connect() -> bool
    async def get_account() -> BrokerAccount
    async def get_positions() -> list[BrokerPosition]
    async def submit_order(order) -> OrderResponse
    async def cancel_order(order_id) -> bool

class PaperBroker(BaseBroker):
    # 本地模拟交易
    # 无需 API 密钥
```

### 4.3 滑点模型

```python
class AlmgrenChrissSlippageModel(BaseSlippageModel):
    """
    Impact = spread/2 + η * σ * (Q/V)^0.5 + γ * (Q/V)
    """

    def calculate(price, quantity, side, market) -> SlippageResult
    def get_fill_price(price, quantity, side, market) -> float
    def estimate_for_trade(symbol, price, quantity, ...) -> dict

class SlippageModelFactory:
    @staticmethod
    def create(config) -> BaseSlippageModel
    @staticmethod
    def get_available_models() -> list[dict]
```

## 5. 依赖检查

### 5.1 后端依赖

```python
# broker_service.py
import httpx              # HTTP 客户端
import structlog          # 日志

# slippage_model.py
import numpy as np        # 数学计算
```

### 5.2 前端依赖

```typescript
// TradingCenter 组件
import { Row, Col, Table, Tag, Button, Form, ... } from 'antd'
import { Card } from '@/components/ui'
import { BrokerType, OrderResponse, ... } from '@/types/trading'
```

## 6. 编码规范检查

### 6.1 中文字符编码

所有中文使用 Unicode 转义序列：
```typescript
'\u8ba2\u5355\u5df2\u63d0\u4ea4'  // 订单已提交
'\u5238\u5546\u8fde\u63a5'        // 券商连接
```

### 6.2 类型安全

- 后端：Pydantic 模型验证
- 前端：TypeScript 严格类型
- API：FastAPI 自动生成 OpenAPI

## 7. 功能完整性检查

| 功能 | 状态 | 说明 |
|------|------|------|
| Alpaca 对接 | ✅ | REST API, Paper Trading |
| Paper Trading | ✅ | 本地模拟 |
| 订单管理 | ✅ | 提交/取消/查询 |
| 滑点模型 | ✅ | Almgren-Chriss 等 4 种 |
| 持仓查询 | ✅ | 实时持仓 |
| 账户信息 | ✅ | 资金/保证金 |
| API 端点 | ✅ | 16 个端点 |
| 前端组件 | ✅ | 3 个组件 |

## 8. 待优化项

1. **Interactive Brokers 对接**：需要 IB Gateway/TWS
2. **WebSocket 实时推送**：订单状态实时更新
3. **执行算法**：TWAP/VWAP/POV 实现
4. **TCA 分析**：交易成本归因
5. **风险检查**：下单前风险验证

## 9. 总结

Phase 12 代码检查通过：
- ✅ 文件结构完整
- ✅ 数据模型一致
- ✅ API 端点注册正确
- ✅ 服务层设计合理
- ✅ 依赖正确
- ✅ 编码规范符合要求
- ✅ 功能完整

**Phase 12 代码检查完成！**
