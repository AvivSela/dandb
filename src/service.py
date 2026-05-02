import asyncio
from dataclasses import dataclass

from scrapper import MarketWatchScraper
from polygon_client import PolygonClient
from holdings_repository import StockHoldingsRepository


@dataclass(frozen=True)
class StockSummary:
    symbol: str
    amount: int | None
    # Polygon OHLCV
    trade_date: str
    open_price: float
    high: float
    low: float
    close: float
    volume: float
    after_hours: float | None
    pre_market: float | None
    # MarketWatch performance
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str
    period_3_year: str
    period_5_year: str


async def get_stock_summary(
    symbol: str,
    repository: StockHoldingsRepository,
    polygon_client: PolygonClient,
    scraper: MarketWatchScraper,
) -> StockSummary:
    ohlcv, metrics, amount = await asyncio.gather(
        polygon_client.get_daily_open_close(symbol),
        scraper.scrape_performance_metrics(symbol),
        repository.get(symbol),
    )

    return StockSummary(
        symbol=symbol,
        amount=amount,
        trade_date=ohlcv.trade_date,
        open_price=ohlcv.open_price,
        high=ohlcv.high,
        low=ohlcv.low,
        close=ohlcv.close,
        volume=ohlcv.volume,
        after_hours=ohlcv.after_hours,
        pre_market=ohlcv.pre_market,
        period_5_day=metrics.period_5_day,
        period_1_month=metrics.period_1_month,
        period_3_month=metrics.period_3_month,
        ytd=metrics.ytd,
        period_1_year=metrics.period_1_year,
        period_3_year=metrics.period_3_year,
        period_5_year=metrics.period_5_year,
    )
