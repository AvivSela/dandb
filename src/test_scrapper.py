import pytest
import requests
from unittest.mock import patch, Mock
from scrapper import MarketWatchScraper, PerformanceMetrics, StockFetchError, PerformanceDataParseError


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
def mock_session():
    with patch('scrapper.requests.Session') as mock_session_class:
        session = Mock()
        mock_session_class.return_value = session
        response = Mock()
        response.text = SAMPLE_HTML
        response.raise_for_status = Mock()
        session.get.return_value = response
        yield session


class TestMarketWatchScraper:

    def test_returns_performance_metrics_instance(self, mock_session):
        result = MarketWatchScraper().scrape_performance_metrics("WIX")
        assert isinstance(result, PerformanceMetrics)

    def test_returns_correct_values(self, mock_session):
        result = MarketWatchScraper().scrape_performance_metrics("WIX")
        assert result.period_5_day == '5.48%'
        assert result.period_1_month == '11.72%'
        assert result.period_3_month == '-8.34%'
        assert result.ytd == '15.23%'
        assert result.period_1_year == '25.67%'
        assert result.period_3_year == '42.89%'
        assert result.period_5_year == '78.45%'

    def test_calls_correct_url(self, mock_session):
        MarketWatchScraper().scrape_performance_metrics("WIX")
        mock_session.get.assert_called_once()
        url = mock_session.get.call_args[0][0]
        assert url == "https://www.marketwatch.com/investing/stock/WIX"

    def test_handles_missing_periods(self):
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
        with patch('scrapper.requests.Session') as mock_session_class:
            session = Mock()
            mock_session_class.return_value = session
            response = Mock()
            response.text = incomplete_html
            response.raise_for_status = Mock()
            session.get.return_value = response

            with pytest.raises(PerformanceDataParseError):
                MarketWatchScraper().scrape_performance_metrics("WIX")

    def test_handles_http_errors(self):
        with patch('scrapper.requests.Session') as mock_session_class:
            session = Mock()
            mock_session_class.return_value = session
            session.get.side_effect = requests.exceptions.ConnectionError("connection failed")

            with pytest.raises(StockFetchError):
                MarketWatchScraper().scrape_performance_metrics("WIX")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
