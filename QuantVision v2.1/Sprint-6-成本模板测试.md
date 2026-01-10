# Sprint 6: 成本配置 + 模板库 + 最终测试 (4天)

> **文档版本**: 1.0  
> **预计时长**: 4天  
> **前置依赖**: Sprint 5 完成  
> **PRD参考**: 4.4 交易成本配置, 4.13 策略模板库  
> **交付物**: 交易成本配置系统、策略模板库、最终整合测试

---

## 目标

完成交易成本配置系统和策略模板库，进行最终整合测试

---

## Part A: 交易成本配置系统 (1.5天)

### Task 6.1: 成本配置Schema (后端)

**文件**: `backend/app/schemas/trading_cost.py`

**核心模型**:
```python
class CostMode(str, Enum):
    SIMPLE = "simple"          # 简单模式
    PROFESSIONAL = "professional"  # 专业模式

class TradingCostConfig(BaseModel):
    mode: CostMode
    commission_per_share: Decimal  # 佣金 ($/股)
    sec_fee_rate: Decimal          # SEC费用 (固定)
    simple_slippage: float         # 简单模式滑点
    slippage: Optional[SlippageConfig]  # 专业模式滑点
    market_impact: Optional[MarketImpactConfig]  # 市场冲击
    cost_buffer: float             # 成本缓冲
```

**最低成本限制**:
| 成本项 | 最低限制 | 默认值 |
|--------|:--------:|:------:|
| 佣金 | $0.003/股 | $0.005/股 |
| 滑点-大盘股 | 0.02% | 0.05% |
| 滑点-中盘股 | 0.05% | 0.10% |
| 滑点-小盘股 | 0.15% | 0.25% |

---

### Task 6.2: 成本计算服务 (后端)

**文件**: `backend/app/services/cost_service.py`

**核心功能**:
- 成本估算
- 最低限制验证
- Almgren-Chriss市场冲击计算

**市场冲击公式**:
```
市场冲击 = η × σ × √(Q/ADV) × 交易额

η: 冲击系数 (0.05-0.5)
σ: 日波动率
Q: 交易量
ADV: 日均成交量
```

---

### Task 6.3: 成本配置API (后端)

**文件**: `backend/app/api/v1/trading_cost.py`

**端点**:
```
GET  /api/v1/trading-cost/config     - 获取成本配置
PUT  /api/v1/trading-cost/config     - 更新成本配置
POST /api/v1/trading-cost/estimate   - 估算交易成本
GET  /api/v1/trading-cost/defaults   - 获取默认配置
```

---

### Task 6.4: 成本配置前端组件

**文件**: `frontend/src/components/TradingCost/CostConfig.tsx`

**UI设计**:
```
┌─────────────────────────────────────────────────────┐
│ 💰 交易成本设置                      [恢复默认]     │
├─────────────────────────────────────────────────────┤
│ 成本模式: [简单模式(推荐)] [专业模式]               │
├─────────────────────────────────────────────────────┤
│ 佣金: [$] [0.005] [/股]  (最低 $0.003)              │
├─────────────────────────────────────────────────────┤
│ 固定滑点: 0.10%                                     │
│ [──────●──────────] 0.05% - 0.50%                   │
├─────────────────────────────────────────────────────┤
│ 成本缓冲: 20%                                       │
│ [──────────●──────] 0% - 50%                        │
├─────────────────────────────────────────────────────┤
│ ℹ️ 实际成本可能高于估算，建议预留缓冲                │
├─────────────────────────────────────────────────────┤
│                                       [保存设置]    │
└─────────────────────────────────────────────────────┘
```

**验收标准**:
- [ ] 简单/专业模式切换正常
- [ ] 最低限制在UI上生效
- [ ] 配置保存成功

---

## Part B: 策略模板库 (1.5天)

### Task 6.5: 模板Schema (后端)

**文件**: `backend/app/schemas/strategy_template.py`

**核心模型**:
```python
class TemplateCategory(str, Enum):
    VALUE = "value"           # 价值投资
    MOMENTUM = "momentum"     # 动量趋势
    DIVIDEND = "dividend"     # 红利收益
    MULTI_FACTOR = "multi_factor"  # 多因子
    TIMING = "timing"         # 择时轮动
    INTRADAY = "intraday"     # 日内交易

class StrategyTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    difficulty: DifficultyLevel  # beginner/intermediate/advanced
    holding_period: HoldingPeriod
    expected_annual_return: str  # "10-15%"
    risk_level: str              # 低/中/高
    strategy_config: dict        # 7步配置JSON
```

---

### Task 6.6: 预设模板数据

**6个预设模板**:

| 模板名 | 类型 | 难度 | 持仓周期 | 预期年化 | 风险 |
|--------|------|:----:|:--------:|:--------:|:----:|
| 巴菲特价值 | 价值 | ⭐ | 长线 | 10-15% | 低 |
| 动量突破 | 趋势 | ⭐⭐ | 短线 | 15-25% | 中 |
| 低波红利 | 防守 | ⭐ | 长线 | 8-12% | 低 |
| 多因子增强 | 量化 | ⭐⭐⭐ | 中线 | 12-18% | 中 |
| 行业轮动 | 择时 | ⭐⭐⭐ | 中线 | 15-20% | 中 |
| 日内动量 | 日内 | ⭐⭐⭐ | 日内 | 20-40% | 高 |

---

### Task 6.7: 模板服务和API (后端)

**文件**: 
- `backend/app/services/template_service.py`
- `backend/app/api/v1/templates.py`

**端点**:
```
GET  /api/v1/templates              - 模板列表
GET  /api/v1/templates/categories   - 模板分类
GET  /api/v1/templates/{id}         - 模板详情
POST /api/v1/templates/{id}/deploy  - 从模板部署策略
```

---

### Task 6.8: 模板库前端页面

**文件**: `frontend/src/pages/Templates/index.tsx`

**UI设计**:
```
┌─────────────────────────────────────────────────────┐
│ 📚 策略模板库                                       │
│ 选择预设模板，一键部署开始交易                      │
├─────────────────────────────────────────────────────┤
│ [搜索...]  [分类: 全部▼]  [难度: 全部▼]             │
├─────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │ 💎          │ │ 🚀          │ │ 💰          │    │
│ │ 巴菲特价值  │ │ 动量突破    │ │ 低波红利    │    │
│ │ ⭐ 入门     │ │ ⭐⭐ 进阶   │ │ ⭐ 入门     │    │
│ │ 长线        │ │ 短线        │ │ 长线        │    │
│ │ 10-15%      │ │ 15-25%      │ │ 8-12%       │    │
│ │ 风险:低     │ │ 风险:中     │ │ 风险:低     │    │
│ │ 1523人使用  │ │ 892人使用   │ │ 1105人使用  │    │
│ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │ 🔬          │ │ 🔄          │ │ ⚡          │    │
│ │ 多因子增强  │ │ 行业轮动    │ │ 日内动量    │    │
│ │ ⭐⭐⭐ 专业 │ │ ⭐⭐⭐ 专业 │ │ ⭐⭐⭐ 专业 │    │
│ │ 中线        │ │ 中线        │ │ 日内        │    │
│ │ 12-18%      │ │ 15-20%      │ │ 20-40%      │    │
│ │ 风险:中     │ │ 风险:中     │ │ 风险:高     │    │
│ │ 567人使用   │ │ 432人使用   │ │ 289人使用   │    │
│ └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

**验收标准**:
- [ ] 6个模板正确显示
- [ ] 筛选功能正常
- [ ] 模板详情展示完整

---

### Task 6.9: 模板详情和部署

**文件**: `frontend/src/components/Template/TemplateDetail.tsx`

**一键部署流程**:
1. 查看模板详情
2. 输入策略名称
3. 点击"一键部署"
4. 跳转到"我的策略"

**验收标准**:
- [ ] 详情展示完整
- [ ] 一键部署流程顺畅
- [ ] 部署后跳转正确

---

## Part C: 最终整合测试 (1天)

### Task 6.10: 测试场景

#### 场景1: 因子验证流程
```
步骤:
1. 进入 FactorLab 页面
2. 选择一个因子 (如 PE_TTM)
3. 查看因子验证面板
4. 检查IC/IR指标
5. 检查分组收益
6. 检查使用建议
7. 点击"添加到策略"

验收: 所有数据正确，流程顺畅
```

#### 场景2: 归因分析流程
```
步骤:
1. 运行一个策略产生交易记录
2. 等待归因报告自动生成
3. 查看归因报告列表
4. 查看报告详情
5. 检查AI诊断建议

验收: 报告自动生成，诊断有价值
```

#### 场景3: 冲突检测流程
```
步骤:
1. 配置两个策略对同一股票发出相反信号
2. 触发冲突检测
3. 查看冲突弹窗
4. 确认系统建议
5. 选择处理方式
6. 确认冲突解决

验收: 冲突正确检测，决策流程清晰
```

#### 场景4: 成本配置流程
```
步骤:
1. 进入 BacktestCenter 页面
2. 打开成本配置面板
3. 切换简单/专业模式
4. 修改成本参数
5. 验证最低限制
6. 保存配置
7. 运行回测验证成本

验收: 配置保存成功，回测成本正确
```

#### 场景5: 模板使用流程
```
步骤:
1. 进入策略模板库
2. 浏览模板列表
3. 按分类/难度筛选
4. 查看模板详情
5. 输入策略名称
6. 点击一键部署
7. 在"我的策略"中查看

验收: 模板展示完整，部署流程顺畅
```

---

### Task 6.11: Bug修复和优化

**高优先级**:
- [ ] 因子验证数据加载失败的错误处理
- [ ] 归因报告生成超时处理
- [ ] 冲突弹窗倒计时不准确
- [ ] 成本配置最低限制UI提示

**中优先级**:
- [ ] 模板库筛选条件重置
- [ ] IC图表在数据量大时性能
- [ ] 冲突历史列表分页

---

### Task 6.12: 路由注册和页面集成

**后端**: `backend/app/main.py`
```python
from app.api.v1 import trading_cost, templates

app.include_router(trading_cost.router, prefix=settings.API_V1_PREFIX)
app.include_router(templates.router, prefix=settings.API_V1_PREFIX)
```

**前端路由**: `frontend/src/App.tsx`
```tsx
{ path: '/templates', element: <TemplatesPage /> }
```

**侧边栏**: `frontend/src/layouts/MainLayout.tsx`
```tsx
{ key: 'templates', icon: <BookOutlined />, label: '策略模板', path: '/templates' }
```

---

## Sprint 6 完成检查清单

### 成本配置
- [ ] Schema定义完整
- [ ] 最低限制强制执行
- [ ] 成本估算正确
- [ ] 前端配置面板正常

### 策略模板
- [ ] 6个模板数据完整
- [ ] 模板列表展示正常
- [ ] 一键部署功能正常
- [ ] 路由配置正确

### 最终测试
- [ ] 场景1: 因子验证 ✓
- [ ] 场景2: 归因分析 ✓
- [ ] 场景3: 冲突检测 ✓
- [ ] 场景4: 成本配置 ✓
- [ ] 场景5: 模板使用 ✓

### 发布准备
- [ ] 所有测试通过
- [ ] 无阻塞性Bug
- [ ] 文档完整
- [ ] 版本号更新为 v2.1

---

## 新增API端点

```
# 成本配置
GET  /api/v1/trading-cost/config     - 获取成本配置
PUT  /api/v1/trading-cost/config     - 更新成本配置
POST /api/v1/trading-cost/estimate   - 估算交易成本
GET  /api/v1/trading-cost/defaults   - 获取默认配置

# 策略模板
GET  /api/v1/templates              - 模板列表
GET  /api/v1/templates/categories   - 模板分类
GET  /api/v1/templates/{id}         - 模板详情
POST /api/v1/templates/{id}/deploy  - 从模板部署策略
```

---

## 🎉 v2.1 发布

Sprint 6 完成后，QuantVision v2.1 准备发布！

### 发布内容

| 功能模块 | 完成情况 |
|----------|:--------:|
| 我的策略列表 | ✅ |
| 4步部署向导 | ✅ |
| 信号雷达面板 | ✅ |
| 环境切换器 | ✅ |
| PDT状态管理 | ✅ |
| AI连接状态 | ✅ |
| 因子有效性验证 | ✅ |
| 交易归因系统 | ✅ |
| 策略冲突检测 | ✅ |
| 交易成本配置 | ✅ |
| 策略模板库 | ✅ |

### 版本信息

- **版本号**: v2.1.0
- **开发周期**: 26天
- **新增API**: 34个
- **新增组件**: 25个

---

**预计完成时间**: 4天
