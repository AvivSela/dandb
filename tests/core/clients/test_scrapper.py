from unittest.mock import AsyncMock

import pytest

from app.core.clients.scrapper import (
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
        await scraper.scrape_performance_metrics("AAPL")


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
