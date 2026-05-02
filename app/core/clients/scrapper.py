from dataclasses import dataclass

from bs4 import BeautifulSoup
import logging

from app.core.clients.http_client import BaseHTTPClient, HTTPStatusError

logger = logging.getLogger(__name__)


class StockFetchError(Exception):
    pass


class PerformanceDataParseError(Exception):
    pass

_PERIOD_MAP = {
    '5 Day':   'period_5_day',
    '1 Month': 'period_1_month',
    '3 Month': 'period_3_month',
    'YTD':     'ytd',
    '1 Year':  'period_1_year'
}

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


@dataclass(frozen=True)
class PerformanceMetrics:
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "PerformanceMetrics":
        return cls(**{field: data.get(key, '0.00%') for key, field in _PERIOD_MAP.items()})


class MarketWatchScraper:
    _api_url = "https://www.marketwatch.com/investing/stock"

    def __init__(self, client: BaseHTTPClient | None = None, request_headers: dict | None = None, timeout: int = 10):
        self._client = client or BaseHTTPClient(
            headers=request_headers or DEFAULT_REQUEST_HEADERS,
            timeout=10,

        )

    async def _fetch_stock_page(self, stock_symbol: str) -> str:
        url = f"{self._api_url}/{stock_symbol}"
        logger.info("Fetching stock page for %s from %s", stock_symbol, url)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except HTTPStatusError as e:
            raise StockFetchError(f"Failed to fetch stock page for '{stock_symbol}': {e}") from e
        logger.debug("Received %d bytes for %s", len(response.text), stock_symbol)
        return response.text

    async def scrape_performance_metrics(self, stock_symbol: str) -> PerformanceMetrics:
        logger.info("Scraping performance metrics for %s", stock_symbol)
        request_text = await self._fetch_stock_page(stock_symbol)
        performance: dict = self._parse_performance_data(request_text)
        metrics = PerformanceMetrics.from_dict(performance)
        logger.info("Scraped %d/%d periods for %s", len(performance), len(_PERIOD_MAP), stock_symbol)
        return metrics

    @staticmethod
    def _parse_performance_data(html_content: str) -> dict[str, str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        performance_data = {}

        for period in _PERIOD_MAP:
            cell = soup.find('td', class_='table__cell', string=period)  # type: ignore[arg-type]
            if not cell:
                logger.warning("Could not parse period '%s' from HTML", period)
                continue
            next_cell = cell.find_next_sibling('td', class_='table__cell')
            if not next_cell:
                logger.warning("Could not parse period '%s' from HTML", period)
                continue
            value_element = next_cell.find('li', class_='content__item value ignore-color')
            if not value_element:
                logger.warning("Could not parse period '%s' from HTML", period)
                continue
            performance_data[period] = value_element.get_text(strip=True)
            logger.debug("Parsed %s: %s", period, performance_data[period])

        missing = [period for period in _PERIOD_MAP if period not in performance_data]
        if missing:
            raise PerformanceDataParseError(f"Missing performance periods: {missing}")
        return performance_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()
