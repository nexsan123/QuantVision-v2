# Phase 10: 风险系统升级 - 代码检查报告

## 1. 新增文件清单

### 后端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `backend/app/schemas/risk_factor.py` | ~320 | Pydantic 风险模型 |
| `backend/app/services/risk_factor_model.py` | ~400 | 风险因子模型服务 |
| `backend/app/services/stress_test_engine.py` | ~350 | 压力测试引擎 |
| `backend/app/api/v1/risk_advanced.py` | ~380 | 风险 API 端点 |

### 前端文件

| 文件路径 | 行数 | 功能 |
|----------|------|------|
| `frontend/src/types/risk.ts` | ~402 | TypeScript 类型定义 |
| `frontend/src/components/RiskDashboard/RiskMonitorPanel.tsx` | ~240 | 实时监控面板 |
| `frontend/src/components/RiskDashboard/RiskDecompositionChart.tsx` | ~200 | 风险分解图表 |
| `frontend/src/components/RiskDashboard/StressTestPanel.tsx` | ~340 | 压力测试面板 |
| `frontend/src/components/RiskDashboard/index.ts` | ~10 | 组件导出 |

## 2. 修改文件清单

| 文件路径 | 修改内容 |
|----------|----------|
| `backend/app/api/v1/__init__.py` | 添加 risk_advanced 模块导出 |
| `backend/app/main.py` | 注册 risk_advanced 路由 |

## 3. 类型定义检查

### 3.1 后端 Pydantic Schema

```python
# risk_factor.py 主要模型

class StyleFactor(str, Enum):
    SIZE = "size"
    VALUE = "value"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    QUALITY = "quality"
    GROWTH = "growth"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"

class IndustryFactor(str, Enum):
    COMMUNICATION_SERVICES = "communication_services"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    # ... 11 个行业因子

class RiskDecompositionResult(BaseModel):
    total_risk: float
    risk_contributions: RiskContributions
    style_risk_details: dict[str, float]
    industry_risk_details: dict[str, float]
    factor_exposures: FactorExposures
    r_squared: float
    tracking_error: float
    active_risk: float

class StressTestResult(BaseModel):
    scenario: StressScenario
    portfolio_impact: PortfolioImpact
    position_impacts: list[PositionImpact]
    risk_metrics_change: RiskMetricsChange
    recommendations: list[str]
```

### 3.2 前端 TypeScript 类型

```typescript
// risk.ts 主要类型

export type StyleFactor = 'size' | 'value' | 'momentum' | ...
export type IndustryFactor = 'communication_services' | ...

export interface RiskDecomposition {
  totalRisk: number
  riskContributions: {
    market: number
    style: number
    industry: number
    specific: number
  }
  factorExposures: {
    market: number
    style: StyleFactorExposures
    industry: Record<string, number>
  }
  // ...
}

export interface StressTestResult {
  scenario: StressScenario
  portfolioImpact: {
    expectedLoss: number
    expectedLossPercent: number
    recoveryDays: number
    liquidationRisk: boolean
  }
  // ...
}
```

## 4. API 端点检查

### 4.1 端点列表

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/risk/advanced/decomposition` | 风险分解 |
| POST | `/api/v1/risk/advanced/factor-exposures` | 因子暴露 |
| POST | `/api/v1/risk/advanced/marginal-risk` | 边际风险 |
| GET | `/api/v1/risk/advanced/scenarios` | 情景列表 |
| POST | `/api/v1/risk/advanced/stress-test/run` | 单次压力测试 |
| POST | `/api/v1/risk/advanced/stress-test/batch` | 批量压力测试 |
| POST | `/api/v1/risk/advanced/stress-test/reverse` | 反向压力测试 |
| GET | `/api/v1/risk/advanced/monitor/status` | 监控状态 |
| GET | `/api/v1/risk/advanced/monitor/dashboard` | 仪表盘 |
| GET | `/api/v1/risk/advanced/limits` | 获取限制 |
| PUT | `/api/v1/risk/advanced/limits` | 更新限制 |
| POST | `/api/v1/risk/advanced/alerts/acknowledge/{id}` | 确认警报 |
| GET | `/api/v1/risk/advanced/alerts/history` | 警报历史 |
| POST | `/api/v1/risk/advanced/report/generate` | 生成报告 |

### 4.2 路由注册确认

```python
# main.py
from app.api.v1 import ..., risk_advanced, ...

app.include_router(
    risk_advanced.router,
    prefix=settings.API_V1_PREFIX,
    tags=["风险系统升级"],
)
```

## 5. 组件依赖检查

### 5.1 后端依赖

```python
# risk_factor_model.py
import numpy as np
import pandas as pd
from scipy import stats

# risk_advanced.py
from app.schemas.risk_factor import (...)
from app.services.risk_factor_model import RiskFactorModel
from app.services.stress_test_engine import StressTestEngine
```

### 5.2 前端依赖

```typescript
// RiskMonitorPanel.tsx
import { Row, Col, Progress, Tag, Alert, ... } from 'antd'
import { Card } from '@/components/ui'
import { RiskMonitorStatus, ... } from '@/types/risk'

// StressTestPanel.tsx
import { StressScenario, StressTestResult, ... } from '@/types/risk'
```

## 6. 编码规范检查

### 6.1 中文字符编码

所有中文字符使用 Unicode 转义序列：
```typescript
// 正确
'\u98ce\u9669\u7cfb\u7edf'  // 风险系统
'\u538b\u529b\u6d4b\u8bd5'  // 压力测试

// 避免直接使用中文（可能导致编码问题）
```

### 6.2 类型安全

- 后端：使用 Pydantic 模型进行请求/响应验证
- 前端：使用 TypeScript 严格类型定义

## 7. 功能完整性检查

| 功能 | 状态 | 说明 |
|------|------|------|
| 风险因子模型 | ✅ | 8 风格 + 11 行业因子 |
| 风险分解 | ✅ | 市场/风格/行业/特质 |
| 压力测试 | ✅ | 11 预置 + 自定义情景 |
| 实时监控 | ✅ | 评分 + 警报系统 |
| 风险限制 | ✅ | 可配置限制 + 状态检查 |
| API 端点 | ✅ | 14 个端点 |
| 前端组件 | ✅ | 3 个核心组件 |

## 8. 待优化项

1. **因子协方差矩阵**：当前使用简化计算，可接入实际因子协方差数据
2. **实时数据**：需接入实时行情计算动态因子暴露
3. **历史情景数据**：可接入实际历史数据进行更精确模拟
4. **单元测试**：需添加 API 端点和服务的单元测试

## 9. 总结

Phase 10 代码检查通过：
- ✅ 文件结构完整
- ✅ 类型定义一致
- ✅ API 端点注册正确
- ✅ 组件依赖正确
- ✅ 编码规范符合要求
- ✅ 功能完整

**Phase 10 代码检查完成！**
