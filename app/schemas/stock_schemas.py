from pydantic import BaseModel, ConfigDict, Field


class PostStockRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"amount": 50}})
    amount: int = Field(gt=0)


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
    def create_from(cls, symbol: str, amount: int):
        return cls(
            message=f"{amount} units of stock {symbol.upper()} were added to your stock record"
        )


class Performance(BaseModel):
    period_5_day: str
    period_1_month: str
    period_3_month: str
    ytd: str
    period_1_year: str


class GetStockResponse(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
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
                    "period_5_day": "+1.2%",
                    "period_1_month": "-0.5%",
                    "period_3_month": "+5.8%",
                    "ytd": "+12.4%",
                    "period_1_year": "+20.1%",
                },
            }
        },
    )
    symbol: str
    amount: int = 0
    status: str = "OK"
    from_date: str = Field(serialization_alias="from")
    open_price: float = Field(serialization_alias="open")
    high: float
    low: float
    close: float
    volume: int
    after_hours: float | None = Field(None, serialization_alias="afterHours")
    pre_market: float | None = Field(None, serialization_alias="preMarket")
    performance: Performance
