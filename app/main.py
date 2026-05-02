from contextlib import asynccontextmanager, AsyncExitStack

from fastapi import FastAPI

# Local imports
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scrapper import MarketWatchScraper
from app.repositories.holdings_repository import StockHoldingsRepository


def get_application() -> FastAPI:
    """
    Factory function to initialize the FastAPI app.
    This makes testing and scaling much easier.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with AsyncExitStack() as stack:
            polygon = await stack.enter_async_context(PolygonClient(settings.POLYGON_API_KEY))
            scraper = await stack.enter_async_context(MarketWatchScraper())
            repository = await StockHoldingsRepository.create("mydb.db")

            app.state.polygon = polygon
            app.state.scraper = scraper
            app.state.repository = repository

            yield

    # 1. Initialize FastAPI with metadata from your config
    _app = FastAPI(
        lifespan=lifespan,
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    _app.include_router(api_router, prefix=settings.API_V1_STR)

    return _app


# The actual app instance used by Uvicorn
app = get_application()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "database": "sqlite"}