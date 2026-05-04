from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.deps import get_stock_service
from app.api.v1.mappers import to_detail_response
from app.schemas.stock_schemas import (
    ErrorResponse,
    StockDetailResponse,
    StockUpdateRequest,
    StockUpdateResponse,
)
from app.services.stock_service import StockService

ShareSymbol = Annotated[str, Path(min_length=1, max_length=10)]

router = APIRouter()


def _openapi_error_entry(description: str, error: str, message: str) -> dict:
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {"example": {"error": error, "message": message}}
        },
    }


@router.get(
    "/{stock_symbol}",
    summary="Get stock summary",
    response_description="OHLC snapshot and performance metrics for the requested symbol",
    responses={
        400: _openapi_error_entry(
            "Invalid stock symbol", "INVALID_REQUEST", "Invalid stock symbol provided."
        ),
        404: _openapi_error_entry(
            "Symbol not found in market data",
            "SYMBOL_NOT_FOUND",
            "No market data found for the requested symbol.",
        ),
        422: _openapi_error_entry(
            "Request validation failed",
            "VALIDATION_ERROR",
            "Request validation failed.",
        ),
        500: _openapi_error_entry(
            "Market data service unavailable",
            "SERVICE_UNAVAILABLE",
            "Market data service is unavailable.",
        ),
        502: _openapi_error_entry(
            "Upstream market data error",
            "MARKET_DATA_ERROR",
            "Market data service returned an error.",
        ),
    },
)
async def get_stock(
    stock_symbol: ShareSymbol, service: StockService = Depends(get_stock_service)
) -> StockDetailResponse:
    symbol = stock_symbol.strip().upper()
    domain = await service.get_stock_summary(symbol)
    return to_detail_response(domain)


@router.post(
    "/{stock_symbol}",
    status_code=201,
    summary="Modify Holding",
    response_description="Confirmation of the adjusted share amount for the requested symbol",
    responses={
        400: _openapi_error_entry(
            "Insufficient shares to complete the deduction",
            "INSUFFICIENT_FUNDS",
            "Insufficient shares to complete deduction for AAPL.",
        ),
        422: _openapi_error_entry(
            "Request validation failed",
            "VALIDATION_ERROR",
            "Request validation failed.",
        ),
    },
)
async def post_stock(
    stock_symbol: ShareSymbol,
    request: StockUpdateRequest,
    service: StockService = Depends(get_stock_service),
) -> StockUpdateResponse:
    symbol = stock_symbol.strip().upper()
    await service.update_holding(symbol, request.amount)
    return StockUpdateResponse.build(symbol, request.amount)
