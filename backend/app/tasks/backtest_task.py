"""
回测异步任务

提供:
- 回测任务提交
- 进度追踪
- 结果存储
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import uuid4

import pandas as pd
import structlog
from celery import states

from app.backtest.engine import BacktestConfig, BacktestEngine
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    name="app.tasks.backtest_task.run_backtest",
    queue="backtest",
    max_retries=2,
    default_retry_delay=60,
)
def run_backtest_task(
    self,
    task_id: str,
    config_dict: dict[str, Any],
    prices_json: str,
    signals_json: str,
    volumes_json: str | None = None,
    benchmark_json: str | None = None,
) -> dict[str, Any]:
    """
    执行回测任务

    Args:
        task_id: 任务 ID
        config_dict: 回测配置字典
        prices_json: 价格数据 JSON
        signals_json: 信号数据 JSON
        volumes_json: 成交量数据 JSON (可选)
        benchmark_json: 基准数据 JSON (可选)

    Returns:
        回测结果字典
    """
    import pandas as pd

    logger.info("开始回测任务", task_id=task_id)

    try:
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"status": "initializing", "progress": 0}
        )

        # 解析配置
        config = BacktestConfig(
            start_date=date.fromisoformat(config_dict["start_date"]),
            end_date=date.fromisoformat(config_dict["end_date"]),
            initial_capital=config_dict.get("initial_capital", 1_000_000.0),
            commission_rate=config_dict.get("commission_rate", 0.001),
            slippage_rate=config_dict.get("slippage_rate", 0.001),
            slippage_model=config_dict.get("slippage_model", "fixed"),
            max_position_pct=config_dict.get("max_position_pct", 0.1),
            max_leverage=config_dict.get("max_leverage", 1.0),
            rebalance_freq=config_dict.get("rebalance_freq", "daily"),
            benchmark=config_dict.get("benchmark", "SPY"),
        )

        # 解析数据
        prices = pd.read_json(prices_json)
        prices.index = pd.to_datetime(prices.index)

        signals = pd.read_json(signals_json)
        signals.index = pd.to_datetime(signals.index)

        volumes = None
        if volumes_json:
            volumes = pd.read_json(volumes_json)
            volumes.index = pd.to_datetime(volumes.index)

        benchmark = None
        if benchmark_json:
            benchmark = pd.read_json(benchmark_json, typ="series")
            benchmark.index = pd.to_datetime(benchmark.index)

        # 更新进度
        self.update_state(
            state="PROGRESS",
            meta={"status": "running", "progress": 10}
        )

        # 创建回测引擎
        engine = BacktestEngine(config)

        # 运行回测
        result = engine.run(
            prices=prices,
            signals=signals,
            volumes=volumes,
            benchmark_prices=benchmark,
        )

        # 更新进度
        self.update_state(
            state="PROGRESS",
            meta={"status": "analyzing", "progress": 90}
        )

        # 序列化结果
        result_dict = {
            "task_id": task_id,
            "status": result.status.value,
            "completed_at": datetime.now().isoformat(),

            # 绩效指标
            "metrics": {
                "total_return": result.total_return,
                "annual_return": result.annual_return,
                "max_drawdown": result.max_drawdown,
                "sharpe_ratio": result.sharpe_ratio,
                "calmar_ratio": result.calmar_ratio,
                "win_rate": result.win_rate,
            },

            # 权益曲线
            "equity_curve": result.equity_curve.to_json(),

            # 月度收益
            "monthly_returns": result.monthly_returns.to_json(),

            # 回撤序列
            "drawdown_series": result.drawdown_series.to_json(),

            # 交易记录
            "trades_count": len(result.trades_history),
        }

        logger.info(
            "回测任务完成",
            task_id=task_id,
            total_return=f"{result.total_return:.2%}",
            sharpe=f"{result.sharpe_ratio:.2f}",
        )

        return result_dict

    except Exception as e:
        logger.error("回测任务失败", task_id=task_id, error=str(e))

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        # 最终失败
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }


class BacktestTaskManager:
    """
    回测任务管理器

    提供:
    - 任务提交
    - 状态查询
    - 结果获取
    """

    @staticmethod
    def submit(
        config: dict[str, Any],
        prices_df: pd.DataFrame,
        signals_df: pd.DataFrame,
        volumes_df: pd.DataFrame | None = None,
        benchmark_series: pd.Series | None = None,
    ) -> str:
        """
        提交回测任务

        Args:
            config: 回测配置
            prices_df: 价格数据
            signals_df: 信号数据
            volumes_df: 成交量数据
            benchmark_series: 基准数据

        Returns:
            任务 ID
        """

        task_id = str(uuid4())

        # 序列化数据
        prices_json = prices_df.to_json()
        signals_json = signals_df.to_json()
        volumes_json = volumes_df.to_json() if volumes_df is not None else None
        benchmark_json = benchmark_series.to_json() if benchmark_series is not None else None

        # 提交任务
        run_backtest_task.apply_async(
            args=[task_id, config, prices_json, signals_json, volumes_json, benchmark_json],
            task_id=task_id,
        )

        logger.info("提交回测任务", task_id=task_id)

        return task_id

    @staticmethod
    def get_status(task_id: str) -> dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            状态信息
        """
        result = run_backtest_task.AsyncResult(task_id)

        if result.state == states.PENDING:
            return {"status": "pending", "progress": 0}
        elif result.state == "PROGRESS":
            return {
                "status": result.info.get("status", "running"),
                "progress": result.info.get("progress", 0),
            }
        elif result.state == states.SUCCESS:
            return {"status": "completed", "progress": 100}
        elif result.state == states.FAILURE:
            return {"status": "failed", "error": str(result.result)}
        else:
            return {"status": result.state.lower(), "progress": 0}

    @staticmethod
    def get_result(task_id: str) -> dict[str, Any] | None:
        """
        获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            回测结果，如果未完成返回 None
        """
        result = run_backtest_task.AsyncResult(task_id)

        if result.ready():
            return result.get()
        return None

    @staticmethod
    def cancel(task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功取消
        """
        run_backtest_task.AsyncResult(task_id).revoke(terminate=True)
        logger.info("取消回测任务", task_id=task_id)
        return True
