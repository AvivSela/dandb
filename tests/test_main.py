import json
from unittest.mock import MagicMock

import pytest
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient

from app.core.clients.polygon_client import PolygonAPIError, PolygonAuthError, PolygonValidationError
from app.core.clients.scraper import PerformanceDataParseError, StockFetchError
from app.main import (
    _external_fetch_handler,
    _insufficient_funds_handler,
    _polygon_api_handler,
    _polygon_auth_handler,
    _polygon_validation_handler,
    _validation_handler,
    app,
)
from app.repositories.holdings_repository import InsufficientFundsException


@pytest.mark.asyncio
async def test_insufficient_funds_handler_returns_400():
    exc = InsufficientFundsException("AAPL")
    response = await _insufficient_funds_handler(MagicMock(), exc)
    assert response.status_code == 400
    assert json.loads(response.body)["error"] == "INSUFFICIENT_FUNDS"


@pytest.mark.asyncio
async def test_polygon_validation_handler_returns_400():
    exc = PolygonValidationError("bad symbol")
    response = await _polygon_validation_handler(MagicMock(), exc)
    assert response.status_code == 400
    assert json.loads(response.body)["error"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_polygon_auth_handler_returns_503():
    exc = PolygonAuthError("unauthorized")
    response = await _polygon_auth_handler(MagicMock(), exc)
    assert response.status_code == 503
    assert json.loads(response.body)["error"] == "SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_polygon_api_handler_404_returns_symbol_not_found():
    exc = PolygonAPIError("not found", status_code=404)
    response = await _polygon_api_handler(MagicMock(), exc)
    assert response.status_code == 404
    assert json.loads(response.body)["error"] == "SYMBOL_NOT_FOUND"


@pytest.mark.asyncio
async def test_polygon_api_handler_non_404_returns_502():
    exc = PolygonAPIError("server error", status_code=500)
    response = await _polygon_api_handler(MagicMock(), exc)
    assert response.status_code == 502
    assert json.loads(response.body)["error"] == "MARKET_DATA_ERROR"


@pytest.mark.asyncio
async def test_stock_fetch_error_handler_returns_502():
    exc = StockFetchError("fetch failed")
    response = await _external_fetch_handler(MagicMock(), exc)
    assert response.status_code == 502
    assert json.loads(response.body)["error"] == "MARKET_DATA_UNAVAILABLE"


@pytest.mark.asyncio
async def test_performance_data_parse_error_handler_returns_502():
    exc = PerformanceDataParseError("parse failed")
    response = await _external_fetch_handler(MagicMock(), exc)
    assert response.status_code == 502
    assert json.loads(response.body)["error"] == "MARKET_DATA_UNAVAILABLE"


@pytest.mark.asyncio
async def test_validation_handler_returns_422():
    exc = RequestValidationError(errors=[])
    response = await _validation_handler(MagicMock(), exc)
    assert response.status_code == 422
    assert json.loads(response.body)["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_health_returns_degraded_before_lifespan():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_health_returns_ok_when_repository_ready():
    app.state.repository = object()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    finally:
        del app.state.repository
