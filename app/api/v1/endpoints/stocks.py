from fastapi import APIRouter, Depends

from app.api.v1.deps import get_stock_service
from app.api.v1.mappers import map_domain_to_response
from app.schemas.stock_schemas import PostStockRequest, GetStockResponse, PostStockResponse
from app.services.stock_service import StockService

router = APIRouter()

@router.get("/{stock_symbol}")
async def get_stock(stock_symbol: str, service: StockService = Depends(get_stock_service)) -> GetStockResponse:

    domain = await service.get_stock_summary(stock_symbol.strip().upper())
    print(domain)
    return map_domain_to_response(domain)

@router.post("/{stock_symbol}")
async def post_stock(stock_symbol: str, request:PostStockRequest, service: StockService = Depends(get_stock_service)) -> PostStockResponse:
    await service.post_stock_summary(stock_symbol, request.amount)
    return PostStockResponse.create_from(stock_symbol.strip().upper(), request.amount)