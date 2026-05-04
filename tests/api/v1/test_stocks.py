from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.api import router
from app.api.v1.deps import get_stock_service
from app.core.config import settings
from app.schemas.domain_schema import (
    DailyOpenClose,
    PerformanceMetrics,
    StockSummaryDomain,
)
from app.services.stock_service import StockService


def _make_domain() -> StockSummaryDomain:
    return StockSummaryDomain(
        daily_snapshot=DailyOpenClose(
            status="OK",
            symbol="AAPL",
            trade_date="2024-03-05",
            open_price=170.0,
            high=172.5,
            low=169.0,
            close=171.5,
            volume=1000000.0,
            after_hours=171.0,
            pre_market=169.5,
        ),
        performance=PerformanceMetrics(
            period_5_day="+1.00%",
            period_1_month="+2.00%",
            period_3_month="+3.00%",
            ytd="+4.00%",
            period_1_year="+5.00%",
        ),
        amount=10,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    svc = AsyncMock(spec=StockService)
    svc.get_stock_summary.return_value = _make_domain()
    svc.update_holding.return_value = None
    return svc


@pytest.fixture
def test_client(mock_service) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=settings.API_V1_STR)
    app.dependency_overrides[get_stock_service] = lambda: mock_service

    @app.get("/health")
    def health_check():
        return {"status": "ok", "database": "sqlite"}

    return TestClient(app)


def test_get_stock_returns_200_with_body(test_client):
    response = test_client.get("/api/v1/stock/AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "from" in data
    assert "open" in data


def test_post_stock_returns_201(test_client):
    response = test_client.post("/api/v1/stock/AAPL", json={"amount": 5})

    assert response.status_code == 201


def test_health_returns_200(test_client):
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
