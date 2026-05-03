from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str
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
    amount: int


class PostStockResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order Executed: BUY 50 AAPL. Your holdings have been updated."
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

        side = "BUY" if amount > 0 else "SELL"
        return cls(
            message=f"Order Executed: {side} {abs(amount)} {symbol.upper()}. Your holdings have been updated."
        )


class Performance(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)
    period_5_day: str = Field(alias="period5Day")
    period_1_month: str = Field(alias="period1Month")
    period_3_month: str = Field(alias="period3Month")
    ytd: str
    period_1_year: str = Field(alias="period1Year")


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
    symbol: str
    amount: int = 0
    status: str = "OK"
    from_date: str = Field(alias="from")
    open_price: float = Field(alias="open")
    high: float
    low: float
    close: float
    volume: int
    after_hours: float | None = Field(None, alias="afterHours")
    pre_market: float | None = Field(None, alias="preMarket")
    performance: Performance
