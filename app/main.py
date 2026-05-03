import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.clients.polygon_client import (
    PolygonAPIError,
    PolygonAuthError,
    PolygonClient,
    PolygonValidationError,
)
from app.core.clients.scrapper import (
    MarketWatchScraper,
    PerformanceDataParseError,
    StockFetchError,
)
from app.core.config import settings
from app.repositories.holdings_repository import (
    InsufficientFundsException,
    StockHoldingsRepository,
)
from app.schemas.stock_schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def _insufficient_funds_handler(
    request: Request, exc: InsufficientFundsException
) -> JSONResponse:
    logger.warning("Insufficient funds for %s", exc.symbol)
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="INSUFFICIENT_FUNDS",
            message=f"Insufficient shares to complete deduction for {exc.symbol}.",
        ).model_dump(),
    )


async def _polygon_validation_handler(
    request: Request, exc: PolygonValidationError
) -> JSONResponse:
    logger.warning("Polygon validation error: %s", exc)
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="INVALID_REQUEST",
            message="Invalid stock symbol provided.",
        ).model_dump(),
    )


async def _polygon_auth_handler(
    request: Request, exc: PolygonAuthError
) -> JSONResponse:
    logger.error("Polygon auth error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="SERVICE_UNAVAILABLE",
            message="Market data service is unavailable.",
        ).model_dump(),
    )


async def _polygon_api_handler(request: Request, exc: PolygonAPIError) -> JSONResponse:
    if exc.status_code == 404:
        logger.warning("Symbol not found: %s", exc)
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="SYMBOL_NOT_FOUND",
                message="No market data found for the requested symbol.",
            ).model_dump(),
        )
    logger.error("Polygon API error (status=%s)", exc.status_code, exc_info=exc)
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(
            error="MARKET_DATA_ERROR",
            message="Market data service returned an error.",
        ).model_dump(),
    )


async def _validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed.",
        ).model_dump(),
    )


async def _external_fetch_handler(
    request: Request, exc: StockFetchError | PerformanceDataParseError
) -> JSONResponse:
    logger.error("External data error", exc_info=exc)
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(
            error="MARKET_DATA_UNAVAILABLE",
            message="Unable to retrieve stock performance data.",
        ).model_dump(),
    )


def get_application() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with AsyncExitStack() as stack:
            polygon = await stack.enter_async_context(
                PolygonClient(
                    settings.POLYGON_API_KEY, timeout=settings.HTTP_REQUEST_TIMEOUT
                )
            )
            scraper = await stack.enter_async_context(
                MarketWatchScraper(timeout=settings.HTTP_REQUEST_TIMEOUT)
            )
            repository = await StockHoldingsRepository.create(settings.DATABASE_URL)

            app.state.polygon = polygon
            app.state.scraper = scraper
            app.state.repository = repository

            yield

    _app = FastAPI(
        lifespan=lifespan,
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    _app.include_router(api_router, prefix=settings.API_V1_STR)

    # Subclasses must be registered before their base class
    _app.add_exception_handler(RequestValidationError, _validation_handler)
    _app.add_exception_handler(InsufficientFundsException, _insufficient_funds_handler)
    _app.add_exception_handler(PolygonValidationError, _polygon_validation_handler)
    _app.add_exception_handler(PolygonAuthError, _polygon_auth_handler)
    _app.add_exception_handler(PolygonAPIError, _polygon_api_handler)
    _app.add_exception_handler(StockFetchError, _external_fetch_handler)
    _app.add_exception_handler(PerformanceDataParseError, _external_fetch_handler)

    return _app


app = get_application()


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
