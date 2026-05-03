import dataclasses


@dataclasses.dataclass(frozen=True)
class DailyOpenClose:
    status: str
    symbol: str
    trade_date: str
    open_price: float
    high: float
    low: float
    close: float
    volume: float
    after_hours: float | None
    pre_market: float | None


@dataclasses.dataclass(frozen=True)
class PerformanceMetrics:
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str


@dataclasses.dataclass(frozen=True)
class StockSummaryDomain:
    performance: PerformanceMetrics
    daily_snapshot: DailyOpenClose
    amount: int
