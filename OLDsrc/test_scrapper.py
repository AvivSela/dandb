import pytest
import httpx
from unittest.mock import AsyncMock, Mock
from scrapper import MarketWatchScraper, PerformanceMetrics, StockFetchError, PerformanceDataParseError
from http_client import BaseHTTPClient


SAMPLE_HTML = """
<html>
<body>
    <table>
        <tr>
            <td class="table__cell">5 Day</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">5.48%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">1 Month</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">11.72%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">3 Month</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">-8.34%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">YTD</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">15.23%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">1 Year</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">25.67%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">3 Year</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">42.89%</li>
            </td>
        </tr>
        <tr>
            <td class="table__cell">5 Year</td>
            <td class="table__cell">
                <li class="content__item value ignore-color">78.45%</li>
            </td>
        </tr>
    </table>
</body>
</html>
"""


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=BaseHTTPClient)
    response = Mock()
    response.text = SAMPLE_HTML
    response.status_code = 200
    response.raise_for_status = Mock()
    client.get = AsyncMock(return_value=response)
    return client, response


class TestMarketWatchScraper:

    async def test_returns_performance_metrics_instance(self, mock_client):
        client, _ = mock_client
        result = await MarketWatchScraper(client=client).scrape_performance_metrics("WIX")
        assert isinstance(result, PerformanceMetrics)

    async def test_returns_correct_values(self, mock_client):
        client, _ = mock_client
        result = await MarketWatchScraper(client=client).scrape_performance_metrics("WIX")
        assert result.period_5_day == '5.48%'
        assert result.period_1_month == '11.72%'
        assert result.period_3_month == '-8.34%'
        assert result.ytd == '15.23%'
        assert result.period_1_year == '25.67%'
        assert result.period_3_year == '42.89%'
        assert result.period_5_year == '78.45%'

    async def test_calls_correct_url(self, mock_client):
        client, _ = mock_client
        await MarketWatchScraper(client=client).scrape_performance_metrics("WIX")
        client.get.assert_called_once()
        url = client.get.call_args[0][0]
        assert url == "https://www.marketwatch.com/investing/stock/WIX"

    async def test_handles_missing_periods(self):
        incomplete_html = """
        <html><body><table>
            <tr>
                <td class="table__cell">5 Day</td>
                <td class="table__cell"><li class="content__item value ignore-color">5.48%</li></td>
            </tr>
            <tr>
                <td class="table__cell">1 Month</td>
                <td class="table__cell"><li class="content__item value ignore-color">11.72%</li></td>
            </tr>
        </table></body></html>
        """
        client = AsyncMock(spec=BaseHTTPClient)
        response = Mock()
        response.text = incomplete_html
        response.status_code = 200
        response.raise_for_status = Mock()
        client.get = AsyncMock(return_value=response)

        with pytest.raises(PerformanceDataParseError):
            await MarketWatchScraper(client=client).scrape_performance_metrics("WIX")

    async def test_handles_http_errors(self):
        client = AsyncMock(spec=BaseHTTPClient)
        client.get = AsyncMock(side_effect=httpx.ConnectError("connection failed"))

        with pytest.raises(StockFetchError):
            await MarketWatchScraper(client=client).scrape_performance_metrics("WIX")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
