import asyncio
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from src.holdings_repository import StockHoldingsRepository
from src.polygon_client import PolygonClient, DailyOpenClose
from src.scrapper import MarketWatchScraper, PerformanceMetrics


class Performance(BaseModel):
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str


class PostStockRequest(BaseModel):
    amount: int


class PostStockResponse(BaseModel):
    message:str
    @classmethod
    def create_from(cls,symbol: str, amount: int):
        return cls(message=f"{amount} units of stock {symbol.strip().upper()} were added to your stock record")


class GetStockResponse(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True
    )
    symbol: str
    amount: int = 0
    status: str = "OK"

    from_date: str = Field(serialization_alias="from")
    open_price: float = Field(serialization_alias="open")
    high: float
    low: float
    close: float
    volume: int
    after_hours: Optional[float] = Field(None, serialization_alias="afterHours")
    pre_market: Optional[float] = Field(None, serialization_alias="preMarket")
    performance: Performance

    @classmethod
    def build_from(cls, daily_open_close:DailyOpenClose, performance_metrics:PerformanceMetrics, amount:int | None):
        safe_amount = amount if amount is not None else 0

        return cls(
            symbol=daily_open_close.symbol,
            amount=safe_amount,
            status=daily_open_close.status,
            from_date=daily_open_close.trade_date,
            open_price=daily_open_close.open_price,
            high=daily_open_close.high,
            low=daily_open_close.low,
            close=daily_open_close.close,
            volume=int(daily_open_close.volume),  # Cast to int as per your requirements
            after_hours=daily_open_close.after_hours,
            pre_market=daily_open_close.pre_market,
            performance=Performance(
                period_5_day=performance_metrics.period_5_day,
                period_1_month=performance_metrics.period_1_month,
                period_3_month=performance_metrics.period_3_month,
                ytd=performance_metrics.ytd,
                period_1_year=performance_metrics.period_1_year
            )
        )

class Service:
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

        return GetStockResponse.build_from(daily_open_close, metrics, amount).model_dump()


    async def post_stock_summary(self, symbol: str, amount: int) -> None:
        normalized_symbol = symbol.strip().upper()
        await self.repository.add_amount(normalized_symbol, amount)
        return None


async def main():
    repo = await StockHoldingsRepository.create("mydb.db")
    service = Service(repo, PolygonClient(), MarketWatchScraper())
    result = await service.get_stock_summary("WIX")
    print(result)

    result = await service.post_stock_summary("wix", 7)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())