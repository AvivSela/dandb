from fastapi import APIRouter, Depends

from app.api.v1.deps import get_stock_service
from app.services.stock_service import StockService

router = APIRouter()

@router.get("/{stock_symbol}")
async def get_stock(stock_symbol: str, service: StockService = Depends(get_stock_service)):
    return await service.get_stock_summary(stock_symbol.strip().upper())

@router.post("/{stock_symbol}")
async def post_stock(stock_symbol: str):
    return [{"post_stock_symbol": stock_symbol}]