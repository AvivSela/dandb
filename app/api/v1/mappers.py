from app.schemas.domain_schema import StockSummaryDomain
from app.schemas.stock_schemas import GetStockResponse, Performance


def map_domain_to_response(domain: StockSummaryDomain) -> GetStockResponse:
    return GetStockResponse(
        # Top-level mapping
        symbol=domain.daily_snapshot.symbol,
        amount=domain.amount,
        status=domain.daily_snapshot.status,
        from_date=domain.daily_snapshot.trade_date,
        # Daily Snapshot mapping (Flattening)
        open_price=domain.daily_snapshot.open_price,
        high=domain.daily_snapshot.high,
        low=domain.daily_snapshot.low,
        close=domain.daily_snapshot.close,
        volume=int(
            domain.daily_snapshot.volume
        ),  # Casting float to int as per your GetStockResponse
        after_hours=domain.daily_snapshot.after_hours,
        pre_market=domain.daily_snapshot.pre_market,
        # Nested Performance mapping
        performance=Performance(
            period_5_day=domain.performance.period_5_day,
            period_1_month=domain.performance.period_1_month,
            period_3_month=domain.performance.period_3_month,
            ytd=domain.performance.ytd,
            period_1_year=domain.performance.period_1_year,
        ),
    )
