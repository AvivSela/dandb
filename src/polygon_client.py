import os
from dataclasses import dataclass
from datetime import date, timedelta
from dotenv import load_dotenv
from urllib.parse import quote

from http_client import BaseHTTPClient, HTTPStatusError


class PolygonError(Exception):
    """Base exception for all Polygon client errors."""


class PolygonAuthError(PolygonError):
    """Raised when the API key is missing or rejected."""


class PolygonValidationError(PolygonError):
    """Raised when input arguments are invalid."""


class PolygonAPIError(PolygonError):
    """Raised when the Polygon API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


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

    def __init__(self, api_key: str | None = None, timeout: int = 10, http_client: BaseHTTPClient | None = None):
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise PolygonAuthError("API key must be provided or set in POLYGON_API_KEY env var")

        self._client = http_client or BaseHTTPClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout
            )


    async def get_daily_open_close(self, stock_symbol: str, trade_date: date | None = None) -> DailyOpenClose:
        if not stock_symbol or not stock_symbol.strip():
            raise PolygonValidationError("stock_symbol must be a non-empty string")

        trade_date_string = self._format_trade_date(trade_date)
        url = f"{self.BASE_URL}/v1/open-close/{quote(stock_symbol)}/{trade_date_string}"

        response = await self._client.get(url)
        try:
            response.raise_for_status()
        except HTTPStatusError as exc:
            raise PolygonAPIError(str(exc), status_code=response.status_code) from exc

        res = DailyOpenClose.from_dict(response.json())
        if res.status != "OK":
            raise PolygonAPIError(f"Unexpected API status: {res.status}")

        return res

    @staticmethod
    def _format_trade_date(trade_date: date | None):
        if trade_date is None:
            trade_date = date.today() - timedelta(days=1)
        return trade_date.strftime("%Y-%m-%d")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()
