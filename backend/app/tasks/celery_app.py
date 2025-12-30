"""
Celery 应用配置

提供异步任务队列支持:
- 回测任务
- 因子计算任务
- 数据同步任务
"""

from celery import Celery
from kombu import Queue

from app.core.config import settings


def create_celery_app() -> Celery:
    """
    创建 Celery 应用实例

    配置:
    - Redis 作为 Broker 和 Backend
    - 任务队列划分
    - 任务重试策略
    """
    app = Celery(
        "quantvision",
        broker=settings.celery_broker,
        backend=settings.celery_backend,
        include=[
            "app.tasks.backtest_task",
        ],
    )

    # 基础配置
    app.conf.update(
        # 任务序列化
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",

        # 时区
        timezone="UTC",
        enable_utc=True,

        # 任务追踪
        task_track_started=True,
        task_time_limit=3600,  # 任务超时 1 小时
        task_soft_time_limit=3300,  # 软超时 55 分钟

        # 结果过期
        result_expires=86400,  # 结果保留 24 小时

        # 并发
        worker_concurrency=4,
        worker_prefetch_multiplier=1,

        # 重试策略
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

    # 任务队列
    app.conf.task_queues = (
        Queue("default", routing_key="default"),
        Queue("backtest", routing_key="backtest.#"),
        Queue("factor", routing_key="factor.#"),
        Queue("data", routing_key="data.#"),
    )

    # 任务路由
    app.conf.task_routes = {
        "app.tasks.backtest_task.*": {"queue": "backtest"},
        "app.tasks.factor_task.*": {"queue": "factor"},
        "app.tasks.data_task.*": {"queue": "data"},
    }

    # 任务默认队列
    app.conf.task_default_queue = "default"
    app.conf.task_default_routing_key = "default"

    return app


# 全局 Celery 应用实例
celery_app = create_celery_app()


# 任务装饰器快捷方式
def task(*args, **kwargs):
    """任务装饰器"""
    return celery_app.task(*args, **kwargs)


# 启动命令示例:
# celery -A app.tasks.celery_app worker --loglevel=info -Q backtest,factor,data,default
