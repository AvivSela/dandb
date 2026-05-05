from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.clients.http_client import BaseHTTPClient, HTTPStatusError
from app.core.clients.polygon_client import (
    PolygonAuthError,
    PolygonClient,
    PolygonValidationError,
)
from app.schemas.domain_schema import DailyOpenClose

VALID_PAYLOAD = {
    "status": "OK",
    "symbol": "AAPL",
    "from": "2024-03-05",
    "open": 170.0,
    "high": 172.5,
    "low": 169.0,
    "close": 171.5,
    "volume": 1000000.0,
    "afterHours": 171.0,
    "preMarket": 169.5,
}


def _ok_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    resp.status_code = 200
    return resp


def _make_client(mock_get: AsyncMock) -> PolygonClient:
    http_client = MagicMock(spec=BaseHTTPClient)
    http_client.get = mock_get
    return PolygonClient(api_key="test-key", http_client=http_client)


async def test_get_daily_open_close_maps_response_to_dataclass():
    mock_get = AsyncMock(return_value=_ok_response(VALID_PAYLOAD))
    client = _make_client(mock_get)

    result = await client.get_daily_open_close("AAPL", date(2024, 3, 5))

    assert isinstance(result, DailyOpenClose)
    assert result.symbol == "AAPL"
    assert result.trade_date == "2024-03-05"
    assert result.open_price == 170.0
    assert result.high == 172.5
    assert result.close == 171.5
    assert result.after_hours == 171.0
    assert result.pre_market == 169.5


async def test_uses_yesterday_date_when_trade_date_is_none():
    mock_get = AsyncMock(return_value=_ok_response(VALID_PAYLOAD))
    client = _make_client(mock_get)

    with patch("app.core.clients.polygon_client.datetime") as mock_dt:
        mock_dt.now.return_value.date.return_value = date(2024, 3, 6)
        await client.get_daily_open_close("YESTERDAY")

    url = mock_get.call_args[0][0]
    assert "2024-03-05" in url


async def test_raises_polygon_auth_error_on_401():
    mock_get = AsyncMock(
        side_effect=HTTPStatusError("HTTP 401 Unauthorized", status_code=401)
    )
    client = _make_client(mock_get)

    with pytest.raises(PolygonAuthError):
        await client.get_daily_open_close("AUTH", date(2024, 1, 1))


async def test_raises_validation_error_for_empty_symbol():
    mock_get = AsyncMock()
    client = _make_client(mock_get)

    with pytest.raises(PolygonValidationError):
        await client.get_daily_open_close("   ")

    mock_get.assert_not_called()


async def test_caches_identical_calls():
    mock_get = AsyncMock(return_value=_ok_response(VALID_PAYLOAD))
    client = _make_client(mock_get)
    trade_date = date(2024, 3, 5)

    await client.get_daily_open_close("CACHETEST", trade_date)
    await client.get_daily_open_close("CACHETEST", trade_date)

    assert mock_get.call_count == 1


def test_calculate_trade_date_returns_day_before_given_date():
    # Tuesday → Monday
    result = PolygonClient._preceding_trade_date_str(date(2024, 3, 5))
    assert result == "2024-03-04"


def test_calculate_trade_date_skips_weekend_when_given_monday():
    # Monday → previous Friday
    result = PolygonClient._preceding_trade_date_str(date(2024, 3, 4))
    assert result == "2024-03-01"


def test_calculate_trade_date_skips_weekend_when_given_saturday():
    # Saturday → previous Friday
    result = PolygonClient._preceding_trade_date_str(date(2024, 3, 2))
    assert result == "2024-03-01"


def test_calculate_trade_date_skips_weekend_when_given_sunday():
    # Sunday → previous Friday
    result = PolygonClient._preceding_trade_date_str(date(2024, 3, 3))
    assert result == "2024-03-01"


async def test_uses_last_friday_when_trade_date_is_none_and_today_is_monday():
    mock_get = AsyncMock(return_value=_ok_response(VALID_PAYLOAD))
    client = _make_client(mock_get)

    with patch("app.core.clients.polygon_client.datetime") as mock_dt:
        mock_dt.now.return_value.date.return_value = date(2024, 3, 4)  # Monday
        await client.get_daily_open_close("WEEKEND")

    url = mock_get.call_args[0][0]
    assert "2024-03-01" in url
