from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.clients.http_client import BaseHTTPClient, HTTPStatusError
from app.core.clients.scraper import (
    MarketWatchScraper,
    PerformanceDataParseError,
    StockFetchError,
)
from app.schemas.domain_schema import PerformanceMetrics

_FULL_HTML = """
<html><body><table>
<tr>
  <td class="table__cell">5 Day</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+1.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">1 Month</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+2.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">3 Month</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+3.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">YTD</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+4.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">1 Year</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+5.00%</li></ul></td>
</tr>
</table></body></html>
"""

_PARTIAL_HTML = """
<html><body><table>
<tr>
  <td class="table__cell">5 Day</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+1.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">1 Month</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+2.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">3 Month</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+3.00%</li></ul></td>
</tr>
<tr>
  <td class="table__cell">YTD</td>
  <td class="table__cell"><ul><li class="content__item value ignore-color">+4.00%</li></ul></td>
</tr>
</table></body></html>
"""


_EXTRA_TABLE_HTML = """
<html><body>
<table>
  <tr><td class="table__cell">Unrelated</td><td class="table__cell">Value</td></tr>
  <tr><td class="table__cell">Also Unrelated</td><td class="table__cell">Value</td></tr>
</table>
<table>
  <tr>
    <td class="table__cell">5 Day</td>
    <td class="table__cell"><ul><li class="content__item value ignore-color">+1.00%</li></ul></td>
  </tr>
  <tr>
    <td class="table__cell">1 Month</td>
    <td class="table__cell"><ul><li class="content__item value ignore-color">+2.00%</li></ul></td>
  </tr>
  <tr>
    <td class="table__cell">3 Month</td>
    <td class="table__cell"><ul><li class="content__item value ignore-color">+3.00%</li></ul></td>
  </tr>
  <tr>
    <td class="table__cell">YTD</td>
    <td class="table__cell"><ul><li class="content__item value ignore-color">+4.00%</li></ul></td>
  </tr>
  <tr>
    <td class="table__cell">1 Year</td>
    <td class="table__cell"><ul><li class="content__item value ignore-color">+5.00%</li></ul></td>
  </tr>
</table>
</body></html>
"""


def test_parse_performance_data_extracts_all_five_periods():
    result = MarketWatchScraper._parse_performance_data(_FULL_HTML)

    assert result["5 Day"] == "+1.00%"
    assert result["1 Month"] == "+2.00%"
    assert result["3 Month"] == "+3.00%"
    assert result["YTD"] == "+4.00%"
    assert result["1 Year"] == "+5.00%"


def test_parse_performance_data_raises_when_period_missing():
    with pytest.raises(PerformanceDataParseError):
        MarketWatchScraper._parse_performance_data(_PARTIAL_HTML)


async def test_scrape_raises_stock_fetch_error_on_http_failure():
    scraper = MarketWatchScraper.__new__(MarketWatchScraper)
    scraper._fetch_stock_page = AsyncMock(side_effect=StockFetchError("HTTP error"))

    with pytest.raises(StockFetchError):
        await scraper._scrape_performance_metrics("AAPL")


def test_parse_performance_data_ignores_extra_cells_from_other_tables():
    result = MarketWatchScraper._parse_performance_data(_EXTRA_TABLE_HTML)

    assert result["5 Day"] == "+1.00%"
    assert result["1 Month"] == "+2.00%"
    assert result["3 Month"] == "+3.00%"
    assert result["YTD"] == "+4.00%"
    assert result["1 Year"] == "+5.00%"


def test_performance_metrics_stores_fields():
    metrics = PerformanceMetrics(
        period_5_day="+1.00%",
        period_1_month="+2.00%",
        period_3_month="+3.00%",
        ytd="+4.00%",
        period_1_year="+5.00%",
    )

    assert metrics.period_5_day == "+1.00%"
    assert metrics.period_1_month == "+2.00%"
    assert metrics.period_3_month == "+3.00%"
    assert metrics.ytd == "+4.00%"
    assert metrics.period_1_year == "+5.00%"


# --- HTML fixtures for warning-branch coverage ---

_MISSING_VALUE_CELL_HTML = """
<html><body><table>
<tr>
  <td class="table__cell">5 Day</td>
</tr>
</table></body></html>
"""

_MISSING_VALUE_ELEMENT_HTML = """
<html><body><table>
<tr>
  <td class="table__cell">5 Day</td>
  <td class="table__cell"><ul><li class="wrong-class">+1.00%</li></ul></td>
</tr>
</table></body></html>
"""


def _make_scraper(mock_get: AsyncMock) -> MarketWatchScraper:
    client = MagicMock(spec=BaseHTTPClient)
    client.get = mock_get
    return MarketWatchScraper(client=client)


# --- _fetch_stock_page ---


async def test_fetch_stock_page_returns_html():
    mock_response = MagicMock()
    mock_response.text = "<html>some content</html>"
    scraper = _make_scraper(AsyncMock(return_value=mock_response))

    result = await scraper._fetch_stock_page("AAPL")

    assert result == "<html>some content</html>"


async def test_fetch_stock_page_raises_stock_fetch_error_on_http_error():
    scraper = _make_scraper(
        AsyncMock(side_effect=HTTPStatusError("HTTP 404", status_code=404))
    )

    with pytest.raises(StockFetchError):
        await scraper._fetch_stock_page("AAPL")


# --- scrape_performance_metrics ---


async def test_scrape_performance_metrics_returns_metrics():
    scraper = MarketWatchScraper.__new__(MarketWatchScraper)
    scraper._fetch_stock_page = AsyncMock(return_value=_FULL_HTML)

    result = await scraper._scrape_performance_metrics("AAPL")

    assert isinstance(result, PerformanceMetrics)
    assert result.period_5_day == "+1.00%"
    assert result.period_1_month == "+2.00%"
    assert result.period_3_month == "+3.00%"
    assert result.ytd == "+4.00%"
    assert result.period_1_year == "+5.00%"


# --- _parse_performance_data warning branches ---


def test_parse_missing_value_cell_raises_parse_error():
    # Row has a known period label but no sibling value cell → warning logged, period skipped
    with pytest.raises(PerformanceDataParseError):
        MarketWatchScraper._parse_performance_data(_MISSING_VALUE_CELL_HTML)


def test_parse_missing_value_element_raises_parse_error():
    # Row has value cell but no matching <li> element → warning logged, period skipped
    with pytest.raises(PerformanceDataParseError):
        MarketWatchScraper._parse_performance_data(_MISSING_VALUE_ELEMENT_HTML)


# --- context manager ---


async def test_context_manager_enters_and_closes():
    client = MagicMock(spec=BaseHTTPClient)
    client.aclose = AsyncMock()
    scraper = MarketWatchScraper(client=client)

    async with scraper as ctx:
        assert ctx is scraper

    client.aclose.assert_awaited_once()


# --- __init__ default client ---


def test_init_creates_default_http_client_when_none_provided():
    scraper = MarketWatchScraper()

    assert isinstance(scraper._client, BaseHTTPClient)
