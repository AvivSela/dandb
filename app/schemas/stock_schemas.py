from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.clients.polygon_client import DailyOpenClose
from app.core.clients.scrapper import PerformanceMetrics


class PostStockRequest(BaseModel):
    amount: int


class PostStockResponse(BaseModel):
    message: str

    @classmethod
    def create_from(cls, symbol: str, amount: int):
        return cls(message=f"{amount} units of stock {symbol.strip().upper()} were added to your stock record")


class Performance(BaseModel):
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str


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
    def build_from(cls, daily_open_close: DailyOpenClose, performance_metrics: PerformanceMetrics, amount: int | None):
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
