# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI REST service that aggregates stock market data by combining official daily OHLC snapshots from the **Polygon.io API** with performance metrics scraped from **MarketWatch**, while persisting user share holdings in a local SQLite database.

---

## Build / Run Commands

Dependencies are managed in `.venv/`. A `pyproject.toml` exists at the project root with ruff configuration.

On Windows, use `.venv\Scripts\` prefix for all tools (e.g. `.venv\Scripts\python.exe`, `.venv\Scripts\ruff.exe`, `.venv\Scripts\pytest.exe`).

```bash
# Install dependencies (if recreating venv)
pip install fastapi uvicorn sqlalchemy aiosqlite httpx pydantic pydantic-settings \
            python-dotenv beautifulsoup4 pytest pytest-asyncio anyio ruff

# Run dev server
uvicorn app.main:app --reload

# Run with explicit host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Requires a `.env` file in the project root:
```
POLYGON_API_KEY=<your_key>
DATABASE_URL=sqlite+aiosqlite:///./sql_app.db   # optional, has a default
```

---

## Linting

```bash
# Check for issues
.venv\Scripts\ruff.exe check app/ tests/

# Auto-fix safe issues
.venv\Scripts\ruff.exe check app/ tests/ --fix

# Format
.venv\Scripts\ruff.exe format app/ tests/
```

Ruff rule **B008** ("function call in default args") is intentionally suppressed in `pyproject.toml` — `Depends()` in default args is the correct FastAPI DI pattern. Do not attempt to refactor it away.

---

## Test Commands

```bash
# Full test suite
pytest

# Single test file
pytest tests/services/test_stock_service.py

# Single test by name
pytest tests/services/test_stock_service.py::test_get_stock_summary

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

Tests use real in-memory SQLite (no DB mocking) and mocked HTTP clients.

---

## Architecture

```
app/
├── main.py                          # App factory, lifespan (AsyncExitStack), /health
├── core/
│   ├── config.py                    # pydantic_settings.BaseSettings — all env vars live here
│   └── clients/
│       ├── http_client.py           # BaseHTTPClient: retry logic (3 attempts, exp backoff)
│       ├── polygon_client.py        # Polygon.io OHLC data, anyio lru_cache
│       └── scraper.py               # MarketWatch HTML scraper, BeautifulSoup
├── api/v1/
│   ├── api.py                       # Router composition (include_router calls only)
│   ├── deps.py                      # All Depends() functions — never define in endpoints
│   ├── mappers.py                   # Domain → Pydantic response (mapping logic lives here only)
│   └── endpoints/
│       └── stocks.py                # GET /{symbol}, POST /{symbol}
├── services/
│   └── stock_service.py             # Business logic; asyncio.gather for parallel I/O
├── repositories/
│   └── holdings_repository.py       # All SQLAlchemy; upsert, add_amount, get, delete
├── models/
│   └── models.py                    # SQLAlchemy ORM models (UserStock)
└── schemas/
    ├── domain_schema.py             # Frozen dataclasses — pure data, no framework deps
    └── stock_schemas.py             # Pydantic request/response models
```

**Layer flow (never skip or reverse):**
```
endpoints → services → repositories → models
    ↓            ↓
 schemas      domain_schema
    ↓
 mappers
```

---

## Coding Standards

### Python Style
- **Python 3.10+** — use `X | Y` union syntax, never `Optional[X]` or `Union[X, Y]`
- **Type hints everywhere** — all parameters and return types
- **Frozen dataclasses** (`@dataclass(frozen=True)`) for domain/value objects
- No `print()` — use `logging.getLogger(__name__)`
- No module-level side effects (`load_dotenv()`, network calls) outside `main.py`
- No unused imports

### Async
- All I/O must be `async`; never block inside an async function
- `asyncio.gather` for parallel independent calls
- `AsyncExitStack` in lifespan for multiple async context managers
- Async class init uses `@classmethod async def create(...)` — never `async def __init__`
- Async caching uses `anyio.functools.lru_cache` (not `functools`)

### Pydantic v2
- `model_config = ConfigDict(...)` — no legacy `class Config`
- `Field(serialization_alias=...)` when only serialization needs the alias (e.g. `from_date → "from"`, `after_hours → "afterHours"` in `StockDetailResponse`)
- `Field(alias=...)` with `populate_by_name=True` when the model must both parse from and serialize to camelCase keys (e.g. `Performance` — populated by alias in the mapper, serialized by alias in the response)
- `json_schema_extra` with a realistic `"example"` block on response models
- `serialize_by_alias=True` in `ConfigDict` when aliases are used
- `StockUpdateResponse.build(symbol, amount)` is the established factory method for building responses from domain data

### Settings
- All config lives in `app/core/config.py`; never read `os.environ` directly
- Optional secrets (e.g. `POLYGON_API_KEY`) should be typed `str | None = None` and validated at startup, not silently passed as `None`

### Dependency Injection
- Singletons stored on `app.state` during lifespan; retrieved via `Depends`
- All `Depends` functions in `deps.py` — never inside endpoint files
- `HTTPException(status_code=500)` when a required `app.state` resource is missing
- Never import clients or repositories directly inside endpoint functions

### Error Handling
- Domain exceptions bubble up; caught and mapped to `JSONResponse` with `ErrorResponse` **at the API layer only** (in `main.py` exception handlers, not via `HTTPException`)
- Never expose raw external service messages to API consumers
- Register handlers in `main.py` with `app.add_exception_handler(...)`; subclasses must be registered before their base class
- Exception hierarchy to be aware of:
  - `PolygonError` (base) → `PolygonAuthError`, `PolygonValidationError`, `PolygonAPIError` (has `.status_code`)
  - `StockFetchError`, `PerformanceDataParseError` (both map to 502)
  - `InsufficientFundsException` (has `.symbol`, maps to 400)

### HTTP Clients
- All clients extend `BaseHTTPClient`; retry/backoff is already handled — don't duplicate it
- Never hard-code `timeout` — always pass it through
- Clients are async context managers; enter via `AsyncExitStack` in lifespan only; never create them inside request handlers
- Do not store mutable state inside `BaseHTTPClient` or client subclasses (they are shared across requests)
- `MarketWatchScraper._parse_performance_data` is CPU-bound (BeautifulSoup); it runs via `loop.run_in_executor` — keep it as a `@staticmethod`, never make it async or inline it into the async method

### Database
- All SQLAlchemy code stays in `app/repositories/` and `app/models/`
- Upsert via `sqlite_insert(...).on_conflict_do_update(...)` — no manual select-then-insert
- `async_sessionmaker(expire_on_commit=False)` to avoid detached-instance lazy-load errors
- WAL mode set once in `StockHoldingsRepository.create` — no PRAGMA calls elsewhere
- Pass `db_path=":memory:"` to `StockHoldingsRepository.create` for in-memory test databases (uses `StaticPool`)

### Testing
- Repository tests use `StockHoldingsRepository.create(":memory:")` — real DB, no mocks
- HTTP client tests mock `BaseHTTPClient.get`
- Service tests inject mock clients via `StockService.__init__`; `PolygonClient` also accepts `http_client=` for lower-level mocking
- Mapper tested independently from endpoints
- `tests/conftest.py` sets `POLYGON_API_KEY=test-key` via `os.environ.setdefault` — new test files don't need to repeat this
- `StockService` is instantiated per-request (no caching in `get_stock_service`)

### OpenAPI
- Every endpoint must have `summary` and `response_description` in the decorator
- Return type annotation (e.g. `-> GetStockResponse`) is the response schema source — omit `response_model=`
- Tags must match what `api.py` declares in `include_router`

---

## What Not To Do

- Do not add `response_model=` when a return type annotation already exists
- Do not create new domain schema files per endpoint — domain objects go in `app/schemas/domain_schema.py`
- Do not add a second router file without a matching `include_router` call in `api.py`
- Do not bypass the service layer by calling the repository directly from an endpoint
- Do not call clients or repository directly in endpoints — always use `Depends`
