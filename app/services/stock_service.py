import asyncio
from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scrapper import MarketWatchScraper
from app.repositories.holdings_repository import StockHoldingsRepository
from app.schemas.stock_schemas import GetStockResponse


class StockService:
    def __init__(self, repository: StockHoldingsRepository,
                 polygon_client: PolygonClient,
                 scraper: MarketWatchScraper,
    ):
        self.repository = repository
        self.polygon_client = polygon_client
        self.scraper = scraper

    async def get_stock_summary(self, symbol: str) -> GetStockResponse:
        normalized_symbol = symbol.strip().upper()
        daily_open_close, metrics, amount = await asyncio.gather(
            self.polygon_client.get_daily_open_close(normalized_symbol),
            self.scraper.scrape_performance_metrics(normalized_symbol),
            self.repository.get(normalized_symbol)
        )

        return GetStockResponse.build_from(daily_open_close, metrics, amount)


    async def post_stock_summary(self, symbol: str, amount: int) -> None:
        normalized_symbol = symbol.strip().upper()
        await self.repository.add_amount(normalized_symbol, amount)
        return None


async def main():
    repo = await StockHoldingsRepository.create("mydb.db")
    service = StockService(repo, PolygonClient(), MarketWatchScraper())
    result = await service.get_stock_summary("WIX")
    print(result)

    result = await service.post_stock_summary("wix", 7)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())