from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.deps import get_stock_service
from app.api.v1.mappers import map_domain_to_response
from app.schemas.stock_schemas import (
    ErrorResponse,
    GetStockResponse,
    PostStockRequest,
    PostStockResponse,
)
from app.services.stock_service import StockService

ShareSymbol = Annotated[str, Path(min_length=1, max_length=10)]

router = APIRouter()


def _error_response(description: str, error: str, message: str) -> dict:
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
        400: _error_response(
            "Invalid stock symbol", "INVALID_REQUEST", "Invalid stock symbol provided."
        ),
        404: _error_response(
            "Symbol not found in market data",
            "SYMBOL_NOT_FOUND",
            "No market data found for the requested symbol.",
        ),
        422: _error_response(
            "Request validation failed",
            "VALIDATION_ERROR",
            "Request validation failed.",
        ),
        500: _error_response(
            "Market data service unavailable",
            "SERVICE_UNAVAILABLE",
            "Market data service is unavailable.",
        ),
        502: _error_response(
            "Upstream market data error",
            "MARKET_DATA_ERROR",
            "Market data service returned an error.",
        ),
    },
)
async def get_stock(
    stock_symbol: ShareSymbol, service: StockService = Depends(get_stock_service)
) -> GetStockResponse:
    symbol = stock_symbol.strip().upper()
    domain = await service.get_stock_summary(symbol)
    return map_domain_to_response(domain)


@router.post(
    "/{stock_symbol}",
    summary="Modify Holding",
    response_description="Confirmation of the adjusted share amount for the requested symbol",
    responses={
        400: _error_response(
            "Insufficient shares to complete the deduction",
            "INSUFFICIENT_FUNDS",
            "Insufficient shares to complete deduction for AAPL.",
        ),
        422: _error_response(
            "Request validation failed",
            "VALIDATION_ERROR",
            "Request validation failed.",
        ),
    },
)
async def post_stock(
    stock_symbol: ShareSymbol,
    request: PostStockRequest,
    service: StockService = Depends(get_stock_service),
) -> PostStockResponse:
    symbol = stock_symbol.strip().upper()
    await service.post_stock_summary(symbol, request.amount)
    return PostStockResponse.create_from(symbol, request.amount)
