"""
Celery 任务模块

提供异步任务支持:
- 回测任务
- 因子计算任务
- 数据同步任务
- 时间止损任务
"""

from app.tasks.backtest_task import run_backtest_task
from app.tasks.celery_app import celery_app
from app.tasks.time_stop_task import (
    TimeStopTask,
    get_time_stop_task,
    start_time_stop_scheduler,
    stop_time_stop_scheduler,
)

__all__ = [
    "celery_app",
    "run_backtest_task",
    "TimeStopTask",
    "get_time_stop_task",
    "start_time_stop_scheduler",
    "stop_time_stop_scheduler",
]
