import os
import requests
from dataclasses import dataclass
from datetime import date, timedelta
from dotenv import load_dotenv
from urllib.parse import quote

@dataclass(frozen=True)
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

    @classmethod
    def from_dict(cls, data: dict) -> "DailyOpenClose":
        return cls(
            status=data["status"],
            symbol=data["symbol"],
            trade_date=data["from"],
            open_price=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            after_hours=data.get("afterHours"),
            pre_market=data.get("preMarket"),
        )

# TODO:  Module-level side effect (src/polygon_client.py:6)
#   load_dotenv() runs on every import. In production environments this can silently override already-set env vars (.env values take precedence unless override=False). Move it to __main__ entry points or the app startup path, not
#   inside a library module.
load_dotenv()


class PolygonClient:
    BASE_URL = "https://api.polygon.io"
    def __init__(self, api_key: str | None = None, timeout: int = 10):
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in POLYGON_API_KEY env var")

        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        self.timeout = timeout

    def get_daily_open_close(self, stock_symbol: str, trade_date: date | None = None) -> DailyOpenClose:
        if not stock_symbol or not stock_symbol.strip():
            raise ValueError("stock_symbol must be a non-empty string")

        trade_date_string = self._format_trade_date(trade_date)

        url = f"{self.BASE_URL}/v1/open-close/{quote(stock_symbol)}/{trade_date_string}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        res = DailyOpenClose.from_dict(response.json())
        if res.status != "OK":
            raise ValueError(f"Unexpected API status: {res.status}")

        return DailyOpenClose.from_dict(response.json())

    @staticmethod
    def _format_trade_date(trade_date: date | None):
        if trade_date is None:
            trade_date = date.today() - timedelta(days=1)

        return trade_date.strftime("%Y-%m-%d")
