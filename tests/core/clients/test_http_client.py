from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.clients.http_client import BaseHTTPClient, HTTPStatusError


def _resp(status_code: int) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status_code
    r.aclose = AsyncMock()
    if status_code >= 400:
        r.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=MagicMock()
        )
    else:
        r.raise_for_status.return_value = None
    return r


@pytest.fixture
def client() -> BaseHTTPClient:
    c = BaseHTTPClient.__new__(BaseHTTPClient)
    c._client = MagicMock()
    c._client.get = AsyncMock()
    return c


@patch("app.core.clients.http_client.asyncio.sleep", new_callable=AsyncMock)
async def test_successful_get_returns_response(mock_sleep, client):
    resp = _resp(200)
    client._client.get.return_value = resp

    result = await client.get("http://example.com")

    assert result is resp
    assert client._client.get.call_count == 1
    mock_sleep.assert_not_called()


@patch("app.core.clients.http_client.asyncio.sleep", new_callable=AsyncMock)
async def test_retries_on_transport_error_then_succeeds(mock_sleep, client):
    ok_resp = _resp(200)
    client._client.get.side_effect = [
        httpx.TransportError("err"),
        httpx.TransportError("err"),
        ok_resp,
    ]

    result = await client.get("http://example.com")

    assert result is ok_resp
    assert client._client.get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("app.core.clients.http_client.asyncio.sleep", new_callable=AsyncMock)
async def test_retries_on_5xx_then_succeeds(mock_sleep, client):
    resp_503 = _resp(503)
    ok_resp = _resp(200)
    client._client.get.side_effect = [resp_503, resp_503, ok_resp]

    result = await client.get("http://example.com")

    assert result is ok_resp
    assert client._client.get.call_count == 3


@patch("app.core.clients.http_client.asyncio.sleep", new_callable=AsyncMock)
async def test_raises_after_max_retries_on_500(mock_sleep, client):
    client._client.get.return_value = _resp(500)

    with pytest.raises(HTTPStatusError):
        await client.get("http://example.com")

    assert client._client.get.call_count == 3


@patch("app.core.clients.http_client.asyncio.sleep", new_callable=AsyncMock)
async def test_does_not_retry_on_4xx(mock_sleep, client):
    client._client.get.return_value = _resp(404)

    with pytest.raises(HTTPStatusError):
        await client.get("http://example.com")

    assert client._client.get.call_count == 1
    mock_sleep.assert_not_called()
