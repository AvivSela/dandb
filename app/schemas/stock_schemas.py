from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ErrorCode = Literal[
    "SYMBOL_NOT_FOUND",
    "INSUFFICIENT_FUNDS",
    "INVALID_REQUEST",
    "SERVICE_UNAVAILABLE",
    "MARKET_DATA_ERROR",
    "MARKET_DATA_UNAVAILABLE",
]


class ErrorResponse(BaseModel):
    error: ErrorCode
    message: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "SYMBOL_NOT_FOUND",
                "message": "No market data found for the requested symbol.",
            }
        }
    )


class PostStockRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"amount": 50}})
    amount: int = Field(
        description="Shares to add (positive) or remove (negative). Zero is a no-op."
    )


class PostStockResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "50 units of stock AAPL were added to your stock record"
            }
        }
    )
    message: str

    @classmethod
    def create_from(cls, symbol: str, amount: int) -> "PostStockResponse":
        if amount == 0:
            return cls(
                message=f"No changes were made to your {symbol.upper()} holdings."
            )

        verb = "added to" if amount > 0 else "removed from"
        return cls(
            message=f"{abs(amount)} units of stock {symbol.upper()} were {verb} your stock record"
        )


class Performance(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)
    period_5_day: str = Field(
        alias="period5Day", description="Price change over the last 5 trading days."
    )
    period_1_month: str = Field(
        alias="period1Month", description="Price change over the last month."
    )
    period_3_month: str = Field(
        alias="period3Month", description="Price change over the last 3 months."
    )
    ytd: str = Field(description="Price change year-to-date.")
    period_1_year: str = Field(
        alias="period1Year", description="Price change over the last year."
    )


class GetStockResponse(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "amount": 150,
                "status": "OK",
                "from": "2023-10-27",
                "open": 172.30,
                "high": 175.67,
                "low": 170.12,
                "close": 173.50,
                "volume": 56430000,
                "afterHours": 173.85,
                "preMarket": 171.10,
                "performance": {
                    "period5Day": "+1.2%",
                    "period1Month": "-0.5%",
                    "period3Month": "+5.8%",
                    "ytd": "+12.4%",
                    "period1Year": "+20.1%",
                },
            }
        },
    )
    symbol: str = Field(description="The stock ticker symbol (e.g. AAPL).")
    amount: int = Field(0, description="User's current share holdings for this symbol.")
    status: Literal["OK"] = "OK"
    from_date: str = Field(
        alias="from", description="Trade date of the snapshot (YYYY-MM-DD)."
    )
    open_price: float = Field(
        alias="open", description="Opening price for the trading day."
    )
    high: float = Field(description="Highest price reached during the trading day.")
    low: float = Field(description="Lowest price reached during the trading day.")
    close: float = Field(description="Closing price for the trading day.")
    volume: int = Field(description="Number of shares traded during the session.")
    after_hours: float | None = Field(
        None, alias="afterHours", description="Post-market closing price, if available."
    )
    pre_market: float | None = Field(
        None, alias="preMarket", description="Pre-market price, if available."
    )
    performance: Performance = Field(
        description="Price performance metrics across multiple time periods."
    )
