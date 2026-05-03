from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.deps import get_stock_service
from app.api.v1.mappers import map_domain_to_response
from app.schemas.stock_schemas import (
    GetStockResponse,
    PostStockRequest,
    PostStockResponse,
)
from app.services.stock_service import StockService

ShareSymbol = Annotated[str, Path(min_length=1, max_length=10)]

router = APIRouter()


@router.get(
    "/{stock_symbol}",
    summary="Get stock summary",
    response_description="OHLC snapshot and performance metrics for the requested symbol",
)
async def get_stock(
    stock_symbol: ShareSymbol, service: StockService = Depends(get_stock_service)
) -> GetStockResponse:
    symbol = stock_symbol.strip().upper()
    domain = await service.get_stock_summary(symbol)
    return map_domain_to_response(domain)


@router.post(
    "/{stock_symbol}",
    summary="Add shares to holding",
    response_description="Confirmation of the added share amount for the requested symbol",
)
async def post_stock(
    stock_symbol: ShareSymbol,
    request: PostStockRequest,
    service: StockService = Depends(get_stock_service),
) -> PostStockResponse:
    symbol = stock_symbol.strip().upper()
    await service.post_stock_summary(symbol, request.amount)
    return PostStockResponse.create_from(symbol, request.amount)
