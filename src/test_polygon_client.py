import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock

from http_client import HTTPStatusError
from polygon_client import (
    DailyOpenClose,
    PolygonClient,
    PolygonAuthError,
    PolygonValidationError,
    PolygonAPIError,
)

SAMPLE_RESPONSE = {
    "status": "OK",
    "symbol": "AAPL",
    "from": "2024-01-15",
    "open": 185.0,
    "high": 188.5,
    "low": 184.0,
    "close": 187.0,
    "volume": 50000000.0,
    "afterHours": 187.5,
    "preMarket": 184.8,
}


@pytest.fixture
def mock_session():
    http_client = AsyncMock()
    response = Mock()
    response.status_code = 200
    response.raise_for_status = Mock()
    response.json.return_value = SAMPLE_RESPONSE.copy()
    http_client.get = AsyncMock(return_value=response)
    return http_client, response


class TestDailyOpenClose:

    def test_from_dict_all_fields(self):
        result = DailyOpenClose.from_dict(SAMPLE_RESPONSE)
        assert result.status == "OK"
        assert result.symbol == "AAPL"
        assert result.trade_date == "2024-01-15"
        assert result.open_price == 185.0
        assert result.after_hours == 187.5
        assert result.pre_market == 184.8

    def test_from_dict_optional_fields_absent(self):
        data = {k: v for k, v in SAMPLE_RESPONSE.items() if k not in ("afterHours", "preMarket")}
        result = DailyOpenClose.from_dict(data)
        assert result.after_hours is None
        assert result.pre_market is None


class TestPolygonClientInit:

    def test_api_key_from_argument(self):
        client = PolygonClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("POLYGON_API_KEY", "env-key")
        client = PolygonClient()
        assert client.api_key == "env-key"

    def test_no_api_key_raises_auth_error(self, monkeypatch):
        monkeypatch.delenv("POLYGON_API_KEY", raising=False)
        with pytest.raises(PolygonAuthError):
            PolygonClient()


class TestFormatTradeDate:

    def test_none_returns_yesterday(self):
        result = PolygonClient._format_trade_date(None)
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_explicit_date_formats_correctly(self):
        result = PolygonClient._format_trade_date(date(2024, 1, 15))
        assert result == "2024-01-15"


class TestGetDailyOpenClose:

    async def test_happy_path_returns_daily_open_close(self, mock_session):
        http_client, _ = mock_session
        client = PolygonClient(api_key="test-key", http_client=http_client)
        result = await client.get_daily_open_close("AAPL", date(2024, 1, 15))
        assert isinstance(result, DailyOpenClose)
        assert result.symbol == "AAPL"

    async def test_blank_symbol_raises_validation_error(self, mock_session):
        http_client, _ = mock_session
        client = PolygonClient(api_key="test-key", http_client=http_client)
        with pytest.raises(PolygonValidationError):
            await client.get_daily_open_close("   ", date(2024, 1, 15))

    async def test_http_error_raises_polygon_api_error_with_status_code(self, mock_session):
        http_client, response = mock_session
        response.status_code = 403
        response.raise_for_status.side_effect = HTTPStatusError("HTTP 403 for url")
        client = PolygonClient(api_key="test-key", http_client=http_client)
        with pytest.raises(PolygonAPIError) as exc_info:
            await client.get_daily_open_close("AAPL", date(2024, 1, 15))
        assert exc_info.value.status_code == 403

    async def test_non_ok_status_raises_polygon_api_error(self, mock_session):
        http_client, response = mock_session
        response.json.return_value = {**SAMPLE_RESPONSE, "status": "ERROR"}
        client = PolygonClient(api_key="test-key", http_client=http_client)
        with pytest.raises(PolygonAPIError):
            await client.get_daily_open_close("AAPL", date(2024, 1, 15))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
