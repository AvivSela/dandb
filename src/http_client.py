import asyncio
import httpx

_RETRY_STATUSES = {429, 500, 502, 503}
_MAX_RETRIES = 3

class HTTPStatusError(Exception):
    pass

class BaseHTTPClient:
    def __init__(self, **kwargs):
        self._client = httpx.AsyncClient(**kwargs)

    async def get(self, url: str) -> httpx.Response:
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.get(url)
            except httpx.TransportError as exc:
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise HTTPStatusError(f"Request to {url} failed after {_MAX_RETRIES} attempts") from exc
            if response.status_code in _RETRY_STATUSES:
                await response.aclose()
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
            try:
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                raise HTTPStatusError(f"HTTP {response.status_code} for {url}") from exc
        raise HTTPStatusError(f"Request to {url} failed after {_MAX_RETRIES} attempts")

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()
