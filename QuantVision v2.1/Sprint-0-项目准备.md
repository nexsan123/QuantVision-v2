# Sprint 0: 项目准备 (1天)

> **文档版本**: 1.0  
> **预计时长**: 1天  
> **前置依赖**: 无  
> **交付物**: 环境确认、代码结构理解

---

## 目标

确保开发环境就绪，理解现有代码结构，规划新增文件位置

---

## Task 0.1: 环境验证

**目标**: 确认现有项目可以正常运行

**步骤**:
```bash
# 1. 进入项目目录
cd quantvision

# 2. 启动后端服务
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 启动前端服务 (新终端)
cd frontend
npm install
npm run dev

# 4. 验证
# - 访问 http://localhost:5173 确认6个页面正常
# - 访问 http://localhost:8000/docs 确认API文档正常
```

**验收标准**:
- [ ] 后端启动无错误
- [ ] 前端启动无错误
- [ ] Dashboard 页面正常显示
- [ ] FactorLab 页面正常显示
- [ ] StrategyBuilder 页面正常显示
- [ ] BacktestCenter 页面正常显示
- [ ] Trading 页面正常显示
- [ ] RiskCenter 页面正常显示

---

## Task 0.2: 代码结构分析

**目标**: 理解现有代码结构和命名规范

**分析内容**:

```
前端目录结构
────────────────────────────────────────────────
frontend/src/
├── pages/           # 页面组件 (每个页面一个文件夹)
├── components/      # 公共组件
├── layouts/         # 布局组件
├── types/           # TypeScript类型定义
├── hooks/           # 自定义Hooks
└── App.tsx          # 路由配置

后端目录结构
────────────────────────────────────────────────
backend/app/
├── api/v1/          # API路由
├── schemas/         # Pydantic模型
├── services/        # 业务服务
├── models/          # 数据库模型
└── main.py          # 应用入口

命名规范
────────────────────────────────────────────────
- 页面: PascalCase (Dashboard, FactorLab)
- 组件: PascalCase (StrategyCard, DeploymentWizard)
- 类型: PascalCase (Strategy, Deployment)
- 服务: snake_case (strategy_service.py)
- API: snake_case (strategy.py)
```

**验收标准**:
- [ ] 理解前端目录结构
- [ ] 理解后端目录结构
- [ ] 确认命名规范

---

## Task 0.3: 新增文件规划

**目标**: 规划v2.1版本新增文件的位置

**新增文件规划**:

```
后端新增 (backend/app/)
────────────────────────────────────────────────
schemas/
  deployment.py          # 部署Schema
  signal_radar.py        # 信号雷达Schema
  factor_validation.py   # 因子验证Schema (Sprint 5)
  trade_record.py        # 交易记录Schema (Sprint 5)
  attribution_report.py  # 归因报告Schema (Sprint 5)
  conflict.py            # 冲突Schema (Sprint 5)
  trading_cost.py        # 成本配置Schema (Sprint 6)
  strategy_template.py   # 模板Schema (Sprint 6)

api/v1/
  deployment.py          # 部署API
  signal_radar.py        # 信号雷达API
  pdt.py                 # PDT管理API
  factor_validation.py   # 因子验证API (Sprint 5)
  attribution.py         # 归因API (Sprint 5)
  conflict.py            # 冲突API (Sprint 5)
  trading_cost.py        # 成本配置API (Sprint 6)
  templates.py           # 模板API (Sprint 6)

services/
  deployment_service.py  # 部署服务
  signal_service.py      # 信号计算服务
  pdt_service.py         # PDT服务
  factor_validation_service.py  # 因子验证服务 (Sprint 5)
  attribution_service.py        # 归因服务 (Sprint 5)
  conflict_service.py           # 冲突服务 (Sprint 5)
  cost_service.py               # 成本服务 (Sprint 6)
  template_service.py           # 模板服务 (Sprint 6)

前端新增 (frontend/src/)
────────────────────────────────────────────────
pages/
  MyStrategies/          # 我的策略列表
  Templates/             # 模板库 (Sprint 6)

components/
  Strategy/              # 策略相关组件
  Deployment/            # 部署相关组件
  SignalRadar/           # 信号雷达组件
  PDT/                   # PDT组件
  AI/                    # AI状态组件
  Factor/                # 因子验证组件 (Sprint 5)
  Attribution/           # 归因组件 (Sprint 5)
  Conflict/              # 冲突组件 (Sprint 5)
  TradingCost/           # 成本配置组件 (Sprint 6)
  Template/              # 模板组件 (Sprint 6)
  common/                # 通用组件

types/
  deployment.ts          # 部署类型
  signalRadar.ts         # 信号雷达类型
  pdt.ts                 # PDT类型
  factorValidation.ts    # 因子验证类型 (Sprint 5)
  attribution.ts         # 归因类型 (Sprint 5)
  conflict.ts            # 冲突类型 (Sprint 5)
  tradingCost.ts         # 成本类型 (Sprint 6)
  template.ts            # 模板类型 (Sprint 6)
```

**验收标准**:
- [ ] 新增文件位置已规划
- [ ] 符合现有命名规范
- [ ] 目录结构清晰

---

## Sprint 0 完成检查清单

- [ ] Task 0.1: 环境验证通过
- [ ] Task 0.2: 代码结构已理解
- [ ] Task 0.3: 新增文件已规划

---

## 下一步

完成后进入 **Sprint 1: 策略管理基础**

---

**预计完成时间**: 1天
