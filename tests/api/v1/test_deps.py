from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.deps import get_repository, get_stock_service
from app.core.clients.polygon_client import PolygonClient
from app.core.clients.scraper import MarketWatchScraper
from app.repositories.holdings_repository import StockHoldingsRepository
from app.services.stock_service import StockService


def test_get_repository_raises_500_when_not_initialized():
    mock_request = MagicMock()
    mock_request.app.state.repository = None

    with pytest.raises(HTTPException) as exc_info:
        get_repository(mock_request)

    assert exc_info.value.status_code == 500


def test_get_stock_service_composes_dependencies_correctly():
    mock_repo = MagicMock(spec=StockHoldingsRepository)
    mock_polygon = MagicMock(spec=PolygonClient)
    mock_scraper = MagicMock(spec=MarketWatchScraper)

    service = get_stock_service(mock_repo, mock_polygon, mock_scraper)

    assert isinstance(service, StockService)
    assert service.repository is mock_repo
    assert service.polygon_client is mock_polygon
    assert service.scraper is mock_scraper
