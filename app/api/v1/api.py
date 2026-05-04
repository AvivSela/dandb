from fastapi import APIRouter

from app.api.v1.endpoints import stocks

api_router = APIRouter()

api_router.include_router(stocks.router, prefix="/stock", tags=["Stocks"])
