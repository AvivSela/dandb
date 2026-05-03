from app.api.v1.mappers import map_domain_to_response
from app.schemas.domain_schema import (
    DailyOpenClose,
    PerformanceMetrics,
    StockSummaryDomain,
)
from app.schemas.stock_schemas import PostStockResponse


def _make_domain(amount: int = 5) -> StockSummaryDomain:
    return StockSummaryDomain(
        daily_snapshot=DailyOpenClose(
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
        ),
        performance=PerformanceMetrics(
            period_5_day="+1.00%",
            period_1_month="+2.00%",
            period_3_month="+3.00%",
            ytd="+4.00%",
            period_1_year="+5.00%",
        ),
        amount=amount,
    )


def test_post_stock_response_create_from_formats_message():
    response = PostStockResponse.create_from("aapl", 10)

    assert "AAPL" in response.message
    assert "10" in response.message


def test_get_stock_response_serializes_field_aliases():
    data = map_domain_to_response(_make_domain()).model_dump(by_alias=True)

    assert "from" in data
    assert "open" in data
    assert "afterHours" in data
    assert "preMarket" in data


def test_get_stock_response_maps_all_fields():
    response = map_domain_to_response(_make_domain(amount=5))

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
