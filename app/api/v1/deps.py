from fastapi import Depends, Request, HTTPException

from app.services.stock_service import StockService
from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scrapper import MarketWatchScraper
from app.core.config import settings
from app.repositories.holdings_repository import StockHoldingsRepository





def get_repository(request: Request) -> StockHoldingsRepository:
    repo = getattr(request.app.state, "repository", None)
    if not repo:
        raise HTTPException(status_code=500, detail="Repository not initialized in application state")
    return repo

def get_polygon_client(request: Request) -> PolygonClient:
    polygon = getattr(request.app.state, "polygon", None)
    if not polygon:
        raise HTTPException(
            status_code=500,
            detail="PolygonClient not initialized in application state"
        )
    return polygon

def get_scraper(request: Request) -> MarketWatchScraper:

    scraper = getattr(request.app.state, "scraper", None)
    if not scraper:
        raise HTTPException(
            status_code=500,
            detail="scraper not initialized in application state"
        )
    return scraper


def get_stock_service(repository: StockHoldingsRepository = Depends(get_repository),
             polygon_client: PolygonClient = Depends(get_polygon_client),
             scraper: MarketWatchScraper = Depends(get_scraper)) -> StockService:



    return StockService(repository, polygon_client, scraper)