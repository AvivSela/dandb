from unittest.mock import AsyncMock

import pytest

from app.core.clients.polygon_client import DailyOpenClose, PolygonClient
from app.core.clients.scrapper import MarketWatchScraper, PerformanceMetrics
from app.repositories.holdings_repository import StockHoldingsRepository
from app.schemas.stock_schemas import GetStockResponse
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
    scraper.scrape_performance_metrics.return_value = _make_performance_metrics()
    return scraper


@pytest.fixture
def service(mock_repo, mock_polygon, mock_scraper) -> StockService:
    return StockService(mock_repo, mock_polygon, mock_scraper)


async def test_get_stock_summary_returns_assembled_response(service, mock_repo):
    result = await service.get_stock_summary("AAPL")

    assert isinstance(result, GetStockResponse)
    assert result.symbol == "AAPL"
    assert result.amount == 10
    assert result.open_price == 170.0
    assert result.performance.period_5_day == "+1.00%"


async def test_get_stock_summary_normalizes_symbol(service, mock_polygon, mock_scraper, mock_repo):
    await service.get_stock_summary(" wix ")

    mock_polygon.get_daily_open_close.assert_called_once_with("WIX")
    mock_scraper.scrape_performance_metrics.assert_called_once_with("WIX")
    mock_repo.get.assert_called_once_with("WIX")


async def test_get_stock_summary_calls_clients_concurrently(service, mock_polygon, mock_scraper):
    await service.get_stock_summary("AAPL")

    mock_polygon.get_daily_open_close.assert_called_once()
    mock_scraper.scrape_performance_metrics.assert_called_once()


async def test_post_stock_summary_calls_add_amount_with_normalized_symbol(service, mock_repo):
    await service.post_stock_summary(" wix ", 7)

    mock_repo.add_amount.assert_called_once_with("WIX", 7)
