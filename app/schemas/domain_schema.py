import dataclasses

from app.core.clients.polygon_client import DailyOpenClose
from app.core.clients.scrapper import PerformanceMetrics


@dataclasses.dataclass(frozen=True)
class StockSummaryDomain:
    performance: PerformanceMetrics
    daily_snapshot: DailyOpenClose
    amount: int