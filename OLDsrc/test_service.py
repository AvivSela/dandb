import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from service import Service
from holdings_repository import StockHoldingsRepository
from polygon_client import DailyOpenClose
from scrapper import PerformanceMetrics


SAMPLE_DOC = DailyOpenClose(
    status="OK", symbol="AAPL", trade_date="2024-01-15",
    open_price=185.0, high=188.5, low=184.0, close=187.0,
    volume=50000000.0, after_hours=187.5, pre_market=184.8,
)

SAMPLE_METRICS = PerformanceMetrics(
    period_5_day="5.48%", period_1_month="11.72%",
    period_3_month="-8.34%", ytd="15.23%", period_1_year="25.67%",
)


@pytest_asyncio.fixture
async def repo():
    return await StockHoldingsRepository.create(":memory:")


@pytest.fixture
def mock_polygon():
    client = AsyncMock()
    client.get_daily_open_close = AsyncMock(return_value=SAMPLE_DOC)
    return client


@pytest.fixture
def mock_scraper():
    scraper = AsyncMock()
    scraper.scrape_performance_metrics = AsyncMock(return_value=SAMPLE_METRICS)
    return scraper


@pytest.fixture
def service(repo, mock_polygon, mock_scraper):
    return Service(repo, mock_polygon, mock_scraper)


class TestGetStockSummary:

    async def test_happy_path(self, service, mock_polygon, mock_scraper):
        result = await service.get_stock_summary("AAPL")
        assert result["symbol"] == "AAPL"
        assert result["amount"] == 0
        assert "open" in result
        assert "from" in result
        assert "afterHours" in result
        assert result["performance"]["period_5_day"] == "5.48%"
        mock_polygon.get_daily_open_close.assert_called_once_with("AAPL")
        mock_scraper.scrape_performance_metrics.assert_called_once_with("AAPL")

    async def test_normalizes_symbol(self, service, mock_polygon, mock_scraper):
        await service.get_stock_summary("  aapl  ")
        mock_polygon.get_daily_open_close.assert_called_once_with("AAPL")
        mock_scraper.scrape_performance_metrics.assert_called_once_with("AAPL")

    async def test_amount_reflects_existing_holding(self, repo, service):
        await repo.upsert("AAPL", 42)
        result = await service.get_stock_summary("AAPL")
        assert result["amount"] == 42


class TestPostStockSummary:

    async def test_updates_amount(self, repo, service):
        result = await service.post_stock_summary("AAPL", 10)
        assert result["amount"] == 10
        assert await repo.get("AAPL") == 10

    async def test_accumulates_on_repeated_calls(self, repo, service):
        await service.post_stock_summary("AAPL", 10)
        result = await service.post_stock_summary("AAPL", 5)
        assert result["amount"] == 15
        assert await repo.get("AAPL") == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
