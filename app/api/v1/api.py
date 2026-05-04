from fastapi import APIRouter

from app.api.v1.endpoints import stocks

router = APIRouter()

router.include_router(stocks.router, prefix="/stock", tags=["Stocks"])
