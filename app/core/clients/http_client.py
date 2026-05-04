import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {500, 502, 503}
_MAX_RETRIES = 3


class HTTPStatusError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BaseHTTPClient:
    def __init__(self, **kwargs):
        self._client = httpx.AsyncClient(**kwargs)

    async def _try_once(self, url: str) -> httpx.Response:
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response
        except httpx.TransportError as exc:
            raise HTTPStatusError(f"Transport error for {url}") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            await exc.response.aclose()
            raise HTTPStatusError(
                f"HTTP {status} for {url}", status_code=status
            ) from exc

    async def get(self, url: str) -> httpx.Response:
        for attempt in range(_MAX_RETRIES):
            try:
                return await self._try_once(url)
            except HTTPStatusError as exc:
                if (
                    exc.status_code is not None
                    and exc.status_code not in _RETRYABLE_STATUS_CODES
                ):
                    raise
                if attempt < _MAX_RETRIES - 1:
                    logger.warning(
                        "Request to %s failed (attempt %d/%d), retrying...",
                        url,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(2**attempt)
        raise HTTPStatusError(f"Request to {url} failed after {_MAX_RETRIES} attempts")

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()
