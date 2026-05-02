from app.core.clients.polygon_client import DailyOpenClose
from app.core.clients.scrapper import PerformanceMetrics
from app.schemas.stock_schemas import GetStockResponse, PostStockResponse


def _make_daily_open_close() -> DailyOpenClose:
    return DailyOpenClose(
        status="OK",
        symbol="AAPL",
        trade_date="2024-03-05",
        open_price=170.0,
        high=172.5,
        low=169.0,
        close=171.5,
        volume=1000000.0,
        after_hours=171.0,
        pre_market=169.5,
    )


def _make_performance_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        period_5_day="+1.00%",
        period_1_month="+2.00%",
        period_3_month="+3.00%",
        ytd="+4.00%",
        period_1_year="+5.00%",
    )


def test_post_stock_response_create_from_formats_message():
    response = PostStockResponse.create_from("aapl", 10)

    assert "AAPL" in response.message
    assert "10" in response.message


def test_get_stock_response_serializes_field_aliases():
    response = GetStockResponse.build_from(_make_daily_open_close(), _make_performance_metrics(), 5)
    data = response.model_dump(by_alias=True)

    assert "from" in data
    assert "open" in data
    assert "afterHours" in data
    assert "preMarket" in data


def test_get_stock_response_build_from_maps_all_fields():
    doc = _make_daily_open_close()
    metrics = _make_performance_metrics()

    response = GetStockResponse.build_from(doc, metrics, 5)

    assert response.symbol == "AAPL"
    assert response.amount == 5
    assert response.status == "OK"
    assert response.from_date == "2024-03-05"
    assert response.open_price == 170.0
    assert response.high == 172.5
    assert response.low == 169.0
    assert response.close == 171.5
    assert response.volume == 1000000
    assert response.after_hours == 171.0
    assert response.pre_market == 169.5
    assert response.performance.period_5_day == "+1.00%"
    assert response.performance.ytd == "+4.00%"
