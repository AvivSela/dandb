import asyncio
from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scrapper import MarketWatchScraper
from app.repositories.holdings_repository import StockHoldingsRepository
from app.schemas.domain_schema import StockSummaryDomain


class StockService:
    def __init__(self, repository: StockHoldingsRepository,
                 polygon_client: PolygonClient,
                 scraper: MarketWatchScraper,
    ):
        self.repository = repository
        self.polygon_client = polygon_client
        self.scraper = scraper

    async def get_stock_summary(self, symbol: str) -> StockSummaryDomain:
        daily_open_close, metrics, amount = await asyncio.gather(
            self.polygon_client.get_daily_open_close(symbol),
            self.scraper.scrape_performance_metrics(symbol),
            self.repository.get(symbol)
        )

        return StockSummaryDomain(performance=metrics,daily_snapshot=daily_open_close, amount=amount or 0)


    async def post_stock_summary(self, symbol: str, amount: int) -> None:
        await self.repository.add_amount(symbol, amount)
        return None
