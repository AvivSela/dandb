
from fastapi import APIRouter, Depends

from app.api.v1.deps import get_stock_service
from app.api.v1.endpoints import stocks  # Import your endpoint modules

api_router = APIRouter()

api_router.include_router(
    stocks.router,
    prefix="/stocks",
    tags=["Stocks", "Shares"]
)