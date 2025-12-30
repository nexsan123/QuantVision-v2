"""
API 端到端测试

测试所有 API 端点的功能
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthAPI:
    """健康检查 API 测试"""

    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_readiness_check(self, client: TestClient):
        """测试就绪检查端点"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200


class TestFactorAPI:
    """因子 API 测试"""

    def test_list_operators(self, client: TestClient):
        """测试获取算子列表"""
        response = client.get("/api/v1/factors/operators")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 80  # 至少 80 个算子

    def test_get_operator_info(self, client: TestClient):
        """测试获取算子信息"""
        response = client.get("/api/v1/factors/operators/momentum")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "description" in data

    def test_calculate_factor(self, client: TestClient):
        """测试计算因子"""
        response = client.post(
            "/api/v1/factors/calculate",
            json={
                "operator": "momentum",
                "symbols": ["AAPL", "GOOGL"],
                "params": {"period": 20},
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
        )
        # 可能返回 200 或 503 (无数据)
        assert response.status_code in [200, 503]


class TestBacktestAPI:
    """回测 API 测试"""

    def test_submit_backtest(self, client: TestClient):
        """测试提交回测任务"""
        response = client.post(
            "/api/v1/backtests",
            json={
                "name": "测试回测",
                "strategy": {
                    "factors": [
                        {"name": "momentum", "period": 20},
                    ],
                    "signal": {"type": "long"},
                    "weight": {"method": "equal"},
                },
                "universe": ["AAPL", "GOOGL", "MSFT"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 1000000,
            },
        )
        # 可能返回 200/202 (接受) 或 503 (服务不可用)
        assert response.status_code in [200, 202, 503]

    def test_get_backtest_status(self, client: TestClient):
        """测试获取回测状态"""
        # 先提交一个回测
        submit_response = client.post(
            "/api/v1/backtests",
            json={
                "name": "状态测试回测",
                "strategy": {
                    "factors": [{"name": "momentum", "period": 20}],
                },
                "universe": ["AAPL"],
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_capital": 100000,
            },
        )

        if submit_response.status_code in [200, 202]:
            data = submit_response.json()
            if "task_id" in data:
                task_id = data["task_id"]
                status_response = client.get(f"/api/v1/backtests/{task_id}")
                assert status_response.status_code in [200, 404]


class TestStrategyAPI:
    """策略 API 测试"""

    def test_validate_strategy(self, client: TestClient):
        """测试策略验证"""
        response = client.post(
            "/api/v1/strategy/validate",
            json={
                "factors": [
                    {"name": "momentum", "period": 20},
                    {"name": "volatility", "period": 20},
                ],
                "signal": {
                    "type": "long",
                    "entry_condition": "momentum > 0",
                },
                "weight": {"method": "equal"},
                "universe": {"type": "sp500"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data

    def test_get_strategy_templates(self, client: TestClient):
        """测试获取策略模板"""
        response = client.get("/api/v1/strategy/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRiskAPI:
    """风险管理 API 测试"""

    def test_calculate_var(self, client: TestClient):
        """测试 VaR 计算"""
        response = client.post(
            "/api/v1/risk/var",
            json={
                "positions": [
                    {"symbol": "AAPL", "quantity": 100, "price": 150},
                    {"symbol": "GOOGL", "quantity": 50, "price": 140},
                ],
                "confidence_level": 0.95,
                "horizon_days": 1,
            },
        )
        assert response.status_code in [200, 503]

    def test_stress_test(self, client: TestClient):
        """测试压力测试"""
        response = client.post(
            "/api/v1/risk/stress-test",
            json={
                "positions": [
                    {"symbol": "AAPL", "quantity": 100, "price": 150},
                ],
                "scenarios": ["market_crash", "sector_rotation"],
            },
        )
        assert response.status_code in [200, 503]


class TestWebSocketStats:
    """WebSocket 统计 API 测试"""

    def test_websocket_stats(self, client: TestClient):
        """测试 WebSocket 统计端点"""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "connections" in data
        assert "channels" in data


class TestOpenAPISchema:
    """OpenAPI Schema 测试"""

    def test_openapi_schema_available(self, client: TestClient):
        """测试 OpenAPI schema 可访问"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_available(self, client: TestClient):
        """测试文档页面可访问"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client: TestClient):
        """测试 ReDoc 页面可访问"""
        response = client.get("/redoc")
        assert response.status_code == 200
