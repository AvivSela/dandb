from unittest.mock import AsyncMock

import pytest

from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scraper import MarketWatchScraper
from app.repositories.holdings_repository import StockHoldingsRepository
from app.schemas.domain_schema import (
    DailyOpenClose,
    PerformanceMetrics,
    StockSummaryDomain,
)
from app.services.stock_service import StockService


def _make_daily_open_close() -> DailyOpenClose:
    return DailyOpenClose(
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
    )


def _make_performance_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        period_5_day="+1.00%",
        period_1_month="+2.00%",
        period_3_month="+3.00%",
        ytd="+4.00%",
        period_1_year="+5.00%",
    )


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock(spec=StockHoldingsRepository)
    repo.get.return_value = 10
    return repo


@pytest.fixture
def mock_polygon() -> AsyncMock:
    polygon = AsyncMock(spec=PolygonClient)
    polygon.get_daily_open_close.return_value = _make_daily_open_close()
    return polygon


@pytest.fixture
def mock_scraper() -> AsyncMock:
    scraper = AsyncMock(spec=MarketWatchScraper)
    scraper.scrape_performance_metrics_cached = AsyncMock(return_value=_make_performance_metrics())
    return scraper


@pytest.fixture
def service(mock_repo, mock_polygon, mock_scraper) -> StockService:
    return StockService(mock_repo, mock_polygon, mock_scraper)


async def test_get_stock_summary_returns_assembled_response(service, mock_repo):
    result = await service.get_stock_summary("AAPL")

    assert isinstance(result, StockSummaryDomain)
    assert result.daily_snapshot.symbol == "AAPL"
    assert result.amount == 10
    assert result.daily_snapshot.open_price == 170.0
    assert result.performance.period_5_day == "+1.00%"


async def test_get_stock_summary_calls_clients_concurrently(
    service, mock_polygon, mock_scraper
):
    await service.get_stock_summary("AAPL")

    mock_polygon.get_daily_open_close.assert_called_once()
    mock_scraper.scrape_performance_metrics_cached.assert_called_once()


async def test_update_holding_buy_calls_update_holding(service, mock_repo):
    await service.update_holding("AAPL", 10)

    mock_repo.update_holding.assert_called_once_with("AAPL", 10)


async def test_update_holding_sell_calls_update_holding(service, mock_repo):
    await service.update_holding("AAPL", -5)

    mock_repo.update_holding.assert_called_once_with("AAPL", -5)


async def test_update_holding_zero_skips_repo(service, mock_repo):
    await service.update_holding("AAPL", 0)

    mock_repo.update_holding.assert_not_called()
