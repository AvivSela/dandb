import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote

from anyio.functools import lru_cache
from pydantic import SecretStr

from app.core.clients.http_client import BaseHTTPClient, HTTPStatusError
from app.schemas.domain_schema import DailyOpenClose

logger = logging.getLogger(__name__)


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


class PolygonClient:
    BASE_URL = "https://api.polygon.io"

    def __init__(
        self,
        api_key: SecretStr,
        timeout: int = 10,
        http_client: BaseHTTPClient | None = None,
    ):
        if not api_key:
            raise PolygonAuthError("API key must be provided")

        self._api_key = api_key

        self._client = http_client or BaseHTTPClient(
            headers={"Authorization": f"Bearer {self._api_key.get_secret_value()}"},
            timeout=timeout,
        )
        self._fetch_open_close_cached = lru_cache(maxsize=1024)(self._fetch_open_close)

    async def get_daily_open_close(
        self, stock_symbol: str, trade_date: date | None = None
    ) -> DailyOpenClose:
        if not stock_symbol or not stock_symbol.strip():
            raise PolygonValidationError("stock_symbol must be a non-empty string")
        trade_date = self._preceding_trade_date_str(trade_date)
        return await self._fetch_open_close_cached(stock_symbol, trade_date)

    async def _fetch_open_close(self, stock_symbol: str, trade_date: str) -> DailyOpenClose:
        logger.debug("cache miss for %s %s", stock_symbol, trade_date)
        url = f"{self.BASE_URL}/v1/open-close/{quote(stock_symbol)}/{trade_date}"

        try:
            response = await self._client.get(url)
        except HTTPStatusError as exc:
            if exc.status_code == 401:
                raise PolygonAuthError(str(exc)) from exc
            raise PolygonAPIError(str(exc), status_code=exc.status_code) from exc

        payload = response.json()

        status = payload.get("status")

        if status != "OK":
            raise PolygonAPIError(f"Unexpected API status: {status}")

        return DailyOpenClose(
            status=payload["status"],
            symbol=payload["symbol"],
            trade_date=payload["from"],
            open_price=payload["open"],
            high=payload["high"],
            low=payload["low"],
            close=payload["close"],
            volume=payload["volume"],
            after_hours=payload.get("afterHours"),
            pre_market=payload.get("preMarket"),
        )

    @staticmethod
    def _preceding_trade_date_str(reference_date: date | None):
        reference_date = reference_date or date.today(ZoneInfo("America/New_York"))
        trade_date_before = _last_weekday_before(reference_date)
        return trade_date_before.strftime("%Y-%m-%d")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()


def _last_weekday_before(reference_date: date):
    candidate = reference_date - timedelta(days=1)
    while candidate.weekday() > 4:
        candidate -= timedelta(days=1)
    return candidate
