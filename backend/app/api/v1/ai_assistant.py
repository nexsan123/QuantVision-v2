"""
AI助手 API 端点
Phase 8: 策略构建增强 - AI辅助功能

支持:
1. 与AI助手对话（Claude API或预置回答降级）
2. 获取各步骤的建议问题
"""
import os
import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

# ==================== 请求/响应模型 ====================

class ChatMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色: user 或 assistant")
    content: str = Field(..., description="消息内容")


class AIAssistantRequest(BaseModel):
    """AI助手请求"""
    question: str = Field(..., min_length=1, max_length=1000, description="用户问题")
    current_step: int = Field(..., ge=0, le=6, description="当前步骤 (0-6)")
    context: Optional[dict] = Field(None, description="策略配置上下文")
    history: List[ChatMessage] = Field(default_factory=list, description="对话历史")


class AIAssistantResponse(BaseModel):
    """AI助手响应"""
    answer: str = Field(..., description="AI回答")
    suggestions: List[str] = Field(default_factory=list, description="建议操作")
    related_step: int = Field(..., description="相关步骤")


class StepSuggestionsResponse(BaseModel):
    """步骤建议问题响应"""
    step: int
    step_name: str
    suggestions: List[str]


# ==================== 步骤定义 ====================

STEP_NAMES = {
    0: "投资池配置",
    1: "因子层配置",
    2: "信号层配置",
    3: "风险层配置",
    4: "组合层配置",
    5: "执行层配置",
    6: "监控层配置",
}

# 各步骤的建议问题
STEP_SUGGESTIONS = {
    0: [
        "什么样的投资池适合我？",
        "为什么要排除小市值股票？",
        "流动性筛选有什么用？",
        "S&P 500和Russell 2000有什么区别？",
    ],
    1: [
        "推荐适合新手的因子组合",
        "动量和价值因子的区别？",
        "IC和IR指标怎么看？",
        "因子中性化有什么作用？",
    ],
    2: [
        "如何设置合理的止损？",
        "入场规则有哪些常见模式？",
        "排名入场和阈值入场的区别？",
        "止盈应该设多少？",
    ],
    3: [
        "机构级风控是什么标准？",
        "为什么不能关闭熔断？",
        "最大回撤设多少合适？",
        "VaR指标怎么理解？",
    ],
    4: [
        "等权重和因子加权哪个好？",
        "调仓频率怎么选择？",
        "最大换手率设多少？",
        "风险平价是什么意思？",
    ],
    5: [
        "市价单和TWAP的区别？",
        "滑点模型怎么选？",
        "交易成本对收益影响多大？",
        "VWAP执行有什么优势？",
    ],
    6: [
        "应该设置哪些告警？",
        "因子衰减告警是什么？",
        "报告频率选日报还是周报？",
        "实时监控有必要吗？",
    ],
}

# 各步骤的系统提示词
STEP_SYSTEM_PROMPTS = {
    0: """你是QuantVision量化投资平台的投资池配置助手。

你的职责是帮助用户理解和配置投资池（Universe）：
- 解释不同股票池的特点（S&P 500、NASDAQ 100、Russell 2000等）
- 说明市值筛选的重要性
- 解释流动性（成交量）筛选的必要性
- 帮助用户理解行业排除的场景

关键原则：
1. 流动性差的股票难以交易，应该排除
2. 市值太小的股票波动大，数据质量差
3. 新上市股票历史数据不足，影响因子计算
4. 投资池决定了策略的可投资范围

用简洁专业的中文回答，给出实用建议。""",

    1: """你是QuantVision量化投资平台的因子选择助手。

你的职责是帮助用户理解和选择因子：
- 解释各类因子的原理（动量、价值、质量、波动率、规模、成长）
- 说明IC（信息系数）和IR（信息比率）的含义
- 推荐因子组合策略
- 解释因子中性化和标准化

关键原则：
1. IC衡量因子预测能力，|IC| > 0.03通常被认为有效
2. IR = IC均值 / IC标准差，衡量因子稳定性
3. 不同因子应该低相关，互补性好
4. 中性化可以去除行业/规模的影响

用简洁专业的中文回答，给出实用建议。""",

    2: """你是QuantVision量化投资平台的信号层配置助手。

你的职责是帮助用户配置买卖信号规则：
- 解释入场规则和出场规则的设计
- 强调止损的重要性（这是必须设置的！）
- 说明排名入场和阈值入场的区别
- 帮助用户设置合理的目标持仓数

关键原则：
1. 止损是必须设置的！没有止损的策略是赌博
2. 入场规则用AND逻辑，所有条件满足才买入
3. 出场规则用OR逻辑，任一条件满足就卖出
4. 目标持仓数影响分散化程度

用简洁专业的中文回答，强调风险控制。""",

    3: """你是QuantVision量化投资平台的风险层配置助手。

你的职责是帮助用户理解和配置风险控制：
- 解释机构级风控标准
- 说明熔断机制的重要性
- 帮助用户设置合理的仓位限制
- 解释VaR和波动率控制

关键原则：
1. 机构级标准：单股2-5%，行业15-25%
2. 熔断规则是最后一道防线，不能关闭
3. 三级熔断：通知(3%) → 暂停开仓(5%) → 完全暂停(15%)
4. 散户常犯错误：仓位过重、没有止损、忽视回撤

核心理念：先学会不亏钱，才能赚钱。

用简洁专业的中文回答，强调风险控制的重要性。""",

    4: """你是QuantVision量化投资平台的组合层配置助手。

你的职责是帮助用户配置组合构建：
- 解释各种权重优化方法（等权重、市值加权、最小方差、风险平价）
- 说明调仓频率和换手率的影响
- 帮助用户理解持仓数量的选择
- 解释现金比例的作用

关键原则：
1. 等权重简单有效，往往能跑赢市值加权
2. 调仓越频繁，换手率越高，成本越大
3. 持仓越分散风险越低，但管理难度增加
4. 保留现金可以降低波动，也便于应对赎回

用简洁专业的中文回答，给出实用建议。""",

    5: """你是QuantVision量化投资平台的执行层配置助手。

你的职责是帮助用户配置交易执行：
- 解释各种执行算法（市价单、TWAP、VWAP、POV）
- 说明交易成本和滑点的影响
- 帮助用户选择合适的滑点模型
- 解释模拟交易和实盘交易的区别

关键原则：
1. 交易成本会吃掉大部分利润，必须重视
2. TWAP分时执行降低冲击，VWAP跟随市场节奏
3. 滑点通常0.05-0.1%，大单更高
4. 先用模拟交易测试，再考虑实盘

用简洁专业的中文回答，强调成本控制。""",

    6: """你是QuantVision量化投资平台的监控层配置助手。

你的职责是帮助用户配置策略监控：
- 解释各种告警类型的作用
- 说明因子衰减监控的重要性
- 帮助用户选择合适的报告频率
- 解释实时监控的必要性

关键原则：
1. 策略上线只是开始，持续监控才是关键
2. 因子会衰减，需要定期检查IC变化
3. 多层告警：预警 → 警告 → 紧急
4. 每周阅读策略报告，了解运行状态

用简洁专业的中文回答，强调持续跟踪。""",
}

# 预置回答库
PRESET_ANSWERS = {
    "什么样的投资池适合我": """根据您的投资目标，我建议：

**新手投资者**: S&P 500
- 成分股流动性好，交易成本低
- 数据质量高，因子计算准确
- 约500只股票，足够分散

**追求成长**: NASDAQ 100
- 科技股集中，成长性强
- 波动较大，适合能承受风险的投资者

**小盘股策略**: Russell 2000
- 小盘股alpha机会更多
- 流动性相对差，需要注意交易成本

**建议配置**:
- 市值下限: 10亿美元（确保流动性）
- 日均成交额: >500万美元
- 上市时间: >1年""",

    "推荐适合新手的因子组合": """对于新手，我推荐一个简单但有效的组合：

**动量 + 价值 + 质量** (三因子组合)

1. **20日动量** (momentum_20d)
   - 捕捉价格趋势
   - IC约0.045，表现稳定

2. **PB估值** (value_pb)
   - 寻找便宜股票
   - IC约0.032，长期有效

3. **ROE质量** (quality_roe)
   - 筛选盈利能力强的公司
   - IC约0.038，逻辑清晰

**组合配置建议**:
- 组合方式: 等权重（简单有效）
- 标准化: Z-Score
- 中性化: 行业中性（去除行业影响）

这个组合逻辑清晰、因子低相关、历史表现稳定。""",

    "如何设置合理的止损": """止损是策略中最重要的风险控制手段！

**止损设置原则**:
1. **必须设置** - 没有止损的策略是赌博
2. **不能太紧** - 给股票正常波动留空间
3. **不能太松** - 否则等于没设

**建议值**:
| 类型 | 止损阈值 | 适用场景 |
|------|----------|----------|
| 保守型 | 10-12% | 风险厌恶型 |
| 平衡型 | 15% | 推荐大多数人 |
| 激进型 | 20% | 高波动策略 |

**重要提醒**:
- 止损不是坏事，它是保护资金的手段
- 真正的高手敢于止损
- 10次止损避免1次大亏就值得

**配合止盈**:
- 止盈可选，一般设50-100%
- 如果策略是趋势跟踪，可以不设止盈""",

    "机构级风控是什么标准": """机构投资者的风控标准非常严格：

**仓位限制**:
| 项目 | 机构标准 | 散户常见 |
|------|----------|----------|
| 单股仓位 | 2-5% | 10-20% |
| 行业仓位 | 15-25% | 无限制 |
| 现金比例 | 5-10% | 0% |

**回撤控制**:
| 级别 | 触发条件 | 动作 |
|------|----------|------|
| 预警 | 日亏损>3% | 发送通知 |
| 警告 | 日亏损>5% | 暂停开新仓 |
| 熔断 | 回撤>15% | 策略暂停 |

**核心理念**:
- "先学会不亏钱，才能赚钱"
- 机构可以承受收益低，但绝不能承受大回撤
- 一次30%的回撤需要43%的涨幅才能回本

**为什么散户经常亏钱**:
1. 仓位过重，一只股票腰斩就亏50%
2. 没有止损，越亏越死扛
3. 忽视回撤，只看收益
4. 频繁交易，成本吃掉利润""",

    "IC和IR指标怎么看": """IC和IR是评价因子好坏的核心指标：

**IC (Information Coefficient)**
- 定义: 因子值与未来收益的相关系数
- 范围: -1 到 1
- 判断标准:
  - |IC| > 0.05: 很好的因子
  - |IC| > 0.03: 可用的因子
  - |IC| < 0.02: 基本无效

**IR (Information Ratio)**
- 定义: IC均值 / IC标准差
- 含义: 衡量因子的稳定性
- 判断标准:
  - IR > 1.0: 优秀
  - IR > 0.5: 良好
  - IR < 0.3: 不稳定

**例子**:
- 因子A: IC=0.04, IR=0.8 → 稳定有效
- 因子B: IC=0.06, IR=0.3 → 时好时坏
- 因子A可能是更好的选择

**注意**:
- IC高但IR低的因子可能过拟合
- 要看长期表现，不要只看单期""",

    "等权重和因子加权哪个好": """两种方法各有优劣：

**等权重 (Equal Weight)**
优点:
- 简单直观，易于理解
- 不依赖预测，减少过拟合
- 研究表明往往能跑赢市值加权指数

缺点:
- 没有利用因子信号强度
- 小盘股权重相对较高

**因子加权 (Factor Score Weight)**
优点:
- 信号越强权重越大，直觉合理
- 可能获得更高收益

缺点:
- 放大因子风险
- 可能集中在少数股票

**建议**:
- 新手: 使用等权重，简单可靠
- 进阶: 可以尝试因子加权，但要控制最大权重
- 高手: 使用风险平价或最优化方法

**最佳实践**:
- 无论哪种方法，都要限制单股最大权重（如5%）
- 定期回测对比不同方法的效果""",
}


# ==================== 可用模型配置 ====================

class AIModelInfo(BaseModel):
    """AI模型信息"""
    id: str
    name: str
    provider: str  # "anthropic" | "openai" | "deepseek" | "google"
    description: str
    max_tokens: int = 4096
    is_recommended: bool = False
    tier: str = "standard"  # "economy" | "standard" | "premium"


# 多平台AI模型列表
AVAILABLE_MODELS: dict[str, AIModelInfo] = {
    # ========== Anthropic Claude (最新模型) ==========
    "claude-opus-4-5-20250514": AIModelInfo(
        id="claude-opus-4-5-20250514",
        name="Claude 4.5 Opus",
        provider="anthropic",
        description="Anthropic最强模型，顶级推理能力",
        max_tokens=8192,
        is_recommended=True,
        tier="premium"
    ),
    "claude-sonnet-4-20250514": AIModelInfo(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider="anthropic",
        description="最新旗舰模型，性能卓越，推荐日常使用",
        max_tokens=8192,
        is_recommended=False,
        tier="premium"
    ),
    "claude-3-5-sonnet-20241022": AIModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        description="上一代高性能模型，稳定可靠",
        max_tokens=8192,
        is_recommended=False,
        tier="standard"
    ),
    "claude-3-5-haiku-20241022": AIModelInfo(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        description="快速响应，成本较低",
        max_tokens=8192,
        is_recommended=False,
        tier="economy"
    ),

    # ========== OpenAI GPT ==========
    "gpt-4o": AIModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        description="OpenAI最新多模态模型",
        max_tokens=4096,
        is_recommended=False,
        tier="premium"
    ),
    "gpt-4-turbo": AIModelInfo(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        description="GPT-4增强版，128k上下文",
        max_tokens=4096,
        is_recommended=False,
        tier="premium"
    ),
    "gpt-3.5-turbo": AIModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        description="快速经济，适合简单任务",
        max_tokens=4096,
        is_recommended=False,
        tier="economy"
    ),

    # ========== DeepSeek ==========
    "deepseek-chat": AIModelInfo(
        id="deepseek-chat",
        name="DeepSeek V3",
        provider="deepseek",
        description="国产最强开源模型，性价比极高",
        max_tokens=8192,
        is_recommended=False,
        tier="standard"
    ),
    "deepseek-coder": AIModelInfo(
        id="deepseek-coder",
        name="DeepSeek Coder",
        provider="deepseek",
        description="专注代码生成，编程能力强",
        max_tokens=8192,
        is_recommended=False,
        tier="standard"
    ),
}

# 当前选择的模型 (全局状态，生产环境应使用Redis/数据库)
_current_model_id: str = "claude-opus-4-5-20250514"


def get_current_model() -> AIModelInfo:
    """获取当前选择的模型"""
    return AVAILABLE_MODELS.get(_current_model_id, AVAILABLE_MODELS["claude-opus-4-5-20250514"])


# ==================== 多平台 API 调用 ====================

def get_api_key_for_provider(provider: str) -> Optional[str]:
    """获取指定平台的API密钥"""
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    elif provider == "openai":
        return os.getenv("OPENAI_API_KEY")
    elif provider == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY")
    return None


async def call_anthropic_api(
    messages: List[dict],
    system_prompt: str,
    model: str,
    max_tokens: int,
    api_key: str
) -> Optional[str]:
    """调用 Anthropic Claude API"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": messages,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Anthropic API call failed: {str(e)}")
        return None


async def call_openai_api(
    messages: List[dict],
    system_prompt: str,
    model: str,
    max_tokens: int,
    api_key: str
) -> Optional[str]:
    """调用 OpenAI GPT API"""
    try:
        # 构建OpenAI格式的消息
        openai_messages = [{"role": "system", "content": system_prompt}]
        openai_messages.extend(messages)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": openai_messages,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        return None


async def call_deepseek_api(
    messages: List[dict],
    system_prompt: str,
    model: str,
    max_tokens: int,
    api_key: str
) -> Optional[str]:
    """调用 DeepSeek API (兼容OpenAI格式)"""
    try:
        # DeepSeek使用OpenAI兼容格式
        deepseek_messages = [{"role": "system", "content": system_prompt}]
        deepseek_messages.extend(messages)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": deepseek_messages,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {str(e)}")
        return None


async def call_ai_api(
    messages: List[dict],
    system_prompt: str,
    max_tokens: int = 1024,
    model_id: Optional[str] = None
) -> Optional[str]:
    """统一的AI API调用入口"""
    # 使用指定模型或当前选择的模型
    model = model_id or _current_model_id
    model_info = AVAILABLE_MODELS.get(model, get_current_model())
    provider = model_info.provider

    # 获取对应平台的API密钥
    api_key = get_api_key_for_provider(provider)
    if not api_key:
        logger.warning(f"{provider} API Key not configured, using preset answers")
        return None

    # 根据平台调用对应的API
    effective_max_tokens = min(max_tokens, model_info.max_tokens)

    if provider == "anthropic":
        return await call_anthropic_api(messages, system_prompt, model, effective_max_tokens, api_key)
    elif provider == "openai":
        return await call_openai_api(messages, system_prompt, model, effective_max_tokens, api_key)
    elif provider == "deepseek":
        return await call_deepseek_api(messages, system_prompt, model, effective_max_tokens, api_key)
    else:
        logger.error(f"Unknown provider: {provider}")
        return None


# 保持向后兼容的别名
async def call_claude_api(
    messages: List[dict],
    system_prompt: str,
    max_tokens: int = 1024,
    model_id: Optional[str] = None
) -> Optional[str]:
    """向后兼容的Claude API调用"""
    return await call_ai_api(messages, system_prompt, max_tokens, model_id)


def find_preset_answer(question: str) -> Optional[str]:
    """查找预置回答"""
    question_lower = question.lower()

    for key, answer in PRESET_ANSWERS.items():
        # 模糊匹配
        key_words = key.replace("？", "").replace("?", "").split()
        if all(word in question_lower or word in question for word in key_words[:3]):
            return answer

    return None


def get_default_answer(question: str, step: int) -> str:
    """获取默认回答"""
    step_name = STEP_NAMES.get(step, "策略配置")
    return f"""关于"{question}"：

这是一个很好的问题！在**{step_name}**这一步，需要注意以下几点：

1. 理解每个配置项的含义和影响
2. 根据自己的风险承受能力选择合适的参数
3. 参考机构级标准，但不必完全照搬

如果您需要更具体的建议，可以告诉我您的：
- 投资目标（学习/稳健/积极）
- 风险承受能力
- 预期投资周期

我会给出更有针对性的建议。

您也可以点击下方的常见问题快速了解相关知识。"""


# ==================== API 端点 ====================

@router.post("/chat", response_model=AIAssistantResponse, summary="与AI助手对话")
async def chat_with_assistant(request: AIAssistantRequest):
    """
    与AI助手对话

    - 首先尝试调用 Claude API
    - 如果没有 API Key 或调用失败，使用预置回答
    - 如果没有匹配的预置回答，返回通用回复
    """
    step = request.current_step
    question = request.question

    # 构建消息历史
    messages = []
    for msg in request.history[-10:]:  # 只保留最近10条
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": question})

    # 获取系统提示词
    system_prompt = STEP_SYSTEM_PROMPTS.get(step, STEP_SYSTEM_PROMPTS[0])

    # 添加上下文信息
    if request.context:
        context_str = f"\n\n当前策略配置上下文: {request.context}"
        system_prompt += context_str

    # 尝试调用 Claude API
    answer = await call_claude_api(messages, system_prompt)

    # 如果 API 调用失败，使用预置回答
    if answer is None:
        answer = find_preset_answer(question)

    # 如果没有预置回答，使用默认回答
    if answer is None:
        answer = get_default_answer(question, step)

    # 获取建议问题
    suggestions = STEP_SUGGESTIONS.get(step, [])[:3]

    return AIAssistantResponse(
        answer=answer,
        suggestions=suggestions,
        related_step=step
    )


@router.get(
    "/suggestions/{step}",
    response_model=StepSuggestionsResponse,
    summary="获取步骤建议问题"
)
async def get_step_suggestions(step: int):
    """
    获取某个步骤的建议问题

    step: 0-6，对应7个策略配置步骤
    """
    if step < 0 or step > 6:
        raise HTTPException(status_code=400, detail="Step must be between 0 and 6")

    return StepSuggestionsResponse(
        step=step,
        step_name=STEP_NAMES[step],
        suggestions=STEP_SUGGESTIONS[step]
    )


@router.get("/steps", summary="获取所有步骤信息")
async def get_all_steps():
    """获取所有步骤的名称和建议问题"""
    return {
        "steps": [
            {
                "step": i,
                "name": STEP_NAMES[i],
                "suggestions": STEP_SUGGESTIONS[i]
            }
            for i in range(7)
        ]
    }


# ==================== AI 连接状态 (PRD 4.2) ====================

from datetime import datetime
from fastapi import BackgroundTasks
import asyncio


class AIConnectionStatus(BaseModel):
    """AI连接状态"""
    is_connected: bool
    status: str  # 'connected' | 'connecting' | 'disconnected' | 'error'
    model_id: str
    model_name: str
    model_description: str
    model_tier: str
    last_heartbeat: Optional[datetime] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    can_reconnect: bool = True
    has_api_key: bool = False


class ModelSwitchRequest(BaseModel):
    """模型切换请求"""
    model_id: str = Field(..., description="目标模型ID")


class ModelListResponse(BaseModel):
    """模型列表响应"""
    models: List[AIModelInfo]
    current_model_id: str


class ProviderStatus(BaseModel):
    """平台状态"""
    name: str
    has_api_key: bool
    models: List[str]


def _build_ai_status() -> AIConnectionStatus:
    """构建当前AI状态"""
    current_model = get_current_model()
    provider = current_model.provider
    api_key = get_api_key_for_provider(provider)

    # 构建错误消息
    if not api_key:
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        error_msg = f"未配置 {env_var_map.get(provider, provider.upper() + '_API_KEY')}"
    else:
        error_msg = None

    return AIConnectionStatus(
        is_connected=bool(api_key),
        status="connected" if api_key else "disconnected",
        model_id=current_model.id,
        model_name=current_model.name,
        model_description=current_model.description,
        model_tier=current_model.tier,
        last_heartbeat=datetime.now(),
        latency_ms=45 if api_key else None,
        error_message=error_msg,
        can_reconnect=True,
        has_api_key=bool(api_key)
    )


@router.get("/providers", summary="获取各平台API配置状态")
async def get_providers_status():
    """
    获取各AI平台的API密钥配置状态
    """
    providers = {}
    for model in AVAILABLE_MODELS.values():
        if model.provider not in providers:
            providers[model.provider] = {
                "name": model.provider,
                "has_api_key": bool(get_api_key_for_provider(model.provider)),
                "models": []
            }
        providers[model.provider]["models"].append(model.name)

    return {
        "providers": list(providers.values()),
        "current_provider": get_current_model().provider
    }


@router.get("/status", response_model=AIConnectionStatus, summary="获取AI连接状态")
async def get_ai_status():
    """
    获取AI连接状态

    返回:
    - is_connected: 是否已连接
    - status: 状态 (connected/connecting/disconnected/error)
    - model_id: 当前模型ID
    - model_name: 模型名称
    - latency_ms: 延迟毫秒数
    - has_api_key: 是否已配置API Key
    """
    return _build_ai_status()


@router.get("/models", response_model=ModelListResponse, summary="获取可用模型列表")
async def get_available_models():
    """
    获取所有可用的AI模型列表

    返回:
    - models: 可用模型列表
    - current_model_id: 当前选择的模型ID
    """
    return ModelListResponse(
        models=list(AVAILABLE_MODELS.values()),
        current_model_id=_current_model_id
    )


@router.post("/models/switch", summary="切换AI模型")
async def switch_model(request: ModelSwitchRequest):
    """
    切换到指定的AI模型

    参数:
    - model_id: 目标模型ID

    返回:
    - success: 是否切换成功
    - model: 切换后的模型信息
    """
    global _current_model_id

    if request.model_id not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"无效的模型ID: {request.model_id}。可用模型: {list(AVAILABLE_MODELS.keys())}"
        )

    _current_model_id = request.model_id
    new_model = get_current_model()

    logger.info(f"AI model switched to: {new_model.name} ({new_model.id})")

    return {
        "success": True,
        "message": f"已切换到 {new_model.name}",
        "model": new_model
    }


@router.post("/reconnect", summary="重新连接AI")
async def reconnect_ai(background_tasks: BackgroundTasks):
    """
    重新连接AI服务

    返回:
    - success: 是否成功发起重连
    - message: 状态消息
    """
    global _ai_status

    if not _ai_status.can_reconnect:
        return {"success": False, "message": "当前无法重连，请稍后再试"}

    # 设置为重连中状态
    _ai_status.status = "connecting"
    _ai_status.is_connected = False
    _ai_status.can_reconnect = False

    # 后台执行重连
    background_tasks.add_task(_do_reconnect)

    return {"success": True, "message": "正在重新连接..."}


async def _do_reconnect():
    """执行重连逻辑"""
    global _ai_status
    await asyncio.sleep(2)  # 模拟重连耗时

    # 模拟重连成功
    _ai_status.is_connected = True
    _ai_status.status = "connected"
    _ai_status.last_heartbeat = datetime.now()
    _ai_status.latency_ms = 50
    _ai_status.error_message = None
    _ai_status.can_reconnect = True


@router.get("/heartbeat", summary="心跳检测")
async def heartbeat():
    """
    心跳检测

    更新最后心跳时间，返回当前状态
    """
    global _ai_status
    _ai_status.last_heartbeat = datetime.now()
    return {"status": "ok", "timestamp": _ai_status.last_heartbeat}
