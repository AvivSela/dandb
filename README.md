![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

# dandb

A FastAPI REST service that aggregates stock market data from two sources — daily OHLC snapshots from the [Polygon.io](https://polygon.io) API and performance metrics scraped from [MarketWatch](https://www.marketwatch.com) — and persists user share holdings in a local SQLite database.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Server](#running-the-server)
7. [API Reference](#api-reference)
8. [Testing](#testing)
9. [Linting and Formatting](#linting-and-formatting)
10. [Project Structure](#project-structure)
11. [Docker](#docker)

---

## Features

- Retrieves daily OHLC (open, high, low, close) snapshots and extended-hours prices via the Polygon.io REST API
- Scrapes multi-period performance metrics (5-day, 1-month, 3-month, YTD, 1-year) from MarketWatch using BeautifulSoup
- Caches Polygon responses per symbol/date with an in-memory LRU cache
- Persists and updates per-user share holdings in SQLite with async I/O and WAL mode enabled
- Validates all environment configuration at startup via Pydantic Settings — the server will not start with a missing API key
- Returns structured, typed error responses for all failure modes (symbol not found, insufficient shares, upstream errors, validation failures)
- Retries transient upstream HTTP failures (500/502/503) up to three times with exponential backoff

---

## Architecture

The service follows a strict layered architecture. Requests flow downward through the layers; no layer skips or calls back upward.

```
HTTP Request
     |
     v
endpoints          (app/api/v1/endpoints/)   receive and validate HTTP input
     |
     v
services           (app/services/)           orchestrate business logic, parallel I/O
     |
     +-----------> repositories  (app/repositories/)  SQLite read/write via SQLAlchemy
     |
     +-----------> clients       (app/core/clients/)  Polygon.io HTTP, MarketWatch scraper
     |
     v
domain_schema      (app/schemas/domain_schema.py)     frozen dataclasses, no framework deps
     |
     v
mappers            (app/api/v1/mappers.py)   translate domain objects to API responses
     |
     v
schemas            (app/schemas/stock_schemas.py)     Pydantic request/response models
     |
     v
HTTP Response
```

**Key design decisions:**

- All singleton dependencies (database engine, HTTP clients) are created once during application lifespan via `AsyncExitStack` and stored on `app.state`. They are injected into endpoints via FastAPI's `Depends` mechanism defined in `deps.py`.
- Domain objects (`DailyOpenClose`, `PerformanceMetrics`, `StockSummaryDomain`) are plain frozen dataclasses with no Pydantic or SQLAlchemy dependency, keeping core logic portable and independently testable.
- Error handling is centralized: domain exceptions bubble up to registered handlers in `main.py` and are translated to typed `ErrorResponse` payloads at that boundary only.

---

## Prerequisites

- Python 3.10 or higher
- A [Polygon.io](https://polygon.io) API key (free tier is sufficient)
- Internet access to reach `api.polygon.io` and `www.marketwatch.com`

---

## Installation

**1. Clone the repository.**

```bash
git clone https://github.com/your-username/dandb.git
cd dandb
```

**2. Create and activate a virtual environment.**

On Linux/macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install runtime dependencies.**

```bash
pip install -r requirements.txt
```

**4. Install development dependencies** (required for tests and linting).

```bash
pip install pytest pytest-asyncio ruff
```

---

## Configuration

Create a `.env` file in the project root. The application reads it automatically at startup.

```env
POLYGON_API_KEY=your_polygon_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `POLYGON_API_KEY` | Yes | — | API key for the Polygon.io REST API. Obtain one at [polygon.io](https://polygon.io). |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./sql_app.db` | SQLAlchemy-format connection string for the SQLite holdings database. |

The application will fail at startup with a validation error if `POLYGON_API_KEY` is absent.

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

On Windows, use the explicit path to the venv binary:

```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload
```

To bind to a specific host and port:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs` once the server is running.

---

## API Reference

All stock endpoints are prefixed with `/api/v1/stock`.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service liveness check |
| `GET` | `/api/v1/stock/{symbol}` | Retrieve OHLC snapshot, performance metrics, and user holdings |
| `POST` | `/api/v1/stock/{symbol}` | Add or remove shares from the user's holdings |

---

### GET /health

Returns a simple liveness indicator.

**Response 200**
```json
{
  "status": "ok"
}
```

---

### GET /api/v1/stock/{symbol}

Fetches the most recent daily OHLC snapshot from Polygon.io and scrapes multi-period performance data from MarketWatch. Both upstream requests run concurrently. Also returns the user's current share holdings for the symbol.

**Path parameter**

| Name | Type | Description |
|---|---|---|
| `symbol` | string | Stock ticker symbol, e.g. `AAPL`. Case-insensitive; normalized to uppercase internally. Maximum 10 characters. |

**Response 200**
```json
{
  "symbol": "AAPL",
  "status": "OK",
  "from": "2023-10-27",
  "open": 172.30,
  "high": 175.67,
  "low": 170.12,
  "close": 173.50,
  "volume": 56430000,
  "afterHours": 173.85,
  "preMarket": 171.10,
  "performance": {
    "period5Day": "+1.2%",
    "period1Month": "-0.5%",
    "period3Month": "+5.8%",
    "ytd": "+12.4%",
    "period1Year": "+20.1%"
  },
  "amount": 150
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `symbol` | string | The normalized ticker symbol |
| `status` | string | Always `"OK"` on success |
| `from` | string | Trade date of the snapshot, `YYYY-MM-DD` |
| `open` | number | Opening price |
| `high` | number | Session high |
| `low` | number | Session low |
| `close` | number | Closing price |
| `volume` | integer | Shares traded during the session |
| `afterHours` | number \| null | Post-market price, if available |
| `preMarket` | number \| null | Pre-market price, if available |
| `performance.period5Day` | string | Price change over the last 5 trading days, e.g. `"+1.2%"` |
| `performance.period1Month` | string | Price change over the last month |
| `performance.period3Month` | string | Price change over the last 3 months |
| `performance.ytd` | string | Year-to-date price change |
| `performance.period1Year` | string | Price change over the last year |
| `amount` | integer | User's current share holdings for this symbol (0 if no record exists) |

**Error responses**

| Status | `error` code | Condition |
|---|---|---|
| 400 | `INVALID_REQUEST` | Ticker symbol failed validation |
| 404 | `SYMBOL_NOT_FOUND` | Polygon.io returned no data for the symbol |
| 422 | `VALIDATION_ERROR` | Malformed request |
| 500 | `SERVICE_UNAVAILABLE` | Polygon.io API key rejected or missing |
| 502 | `MARKET_DATA_ERROR` | Polygon.io returned an unexpected error |
| 502 | `MARKET_DATA_UNAVAILABLE` | MarketWatch data could not be fetched or parsed |

---

### POST /api/v1/stock/{symbol}

Adjusts the user's share holdings for the given symbol. Positive values add shares; negative values remove shares. Holdings cannot go below zero.

**Path parameter**

| Name | Type | Description |
|---|---|---|
| `symbol` | string | Stock ticker symbol, e.g. `AAPL`. Maximum 10 characters. |

**Request body** (`application/json`)

```json
{
  "amount": 50
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `amount` | integer | Yes | Shares to add (positive) or remove (negative). |

**Response 201**
```json
{
  "message": "50 units of stock AAPL were added to your stock record"
}
```

**Error responses**

| Status | `error` code | Condition |
|---|---|---|
| 400 | `INSUFFICIENT_FUNDS` | Deducting more shares than the user currently holds |
| 422 | `VALIDATION_ERROR` | Missing or non-integer `amount` field |

---

All error responses share this shape:

```json
{
  "error": "SYMBOL_NOT_FOUND",
  "message": "No market data found for the requested symbol."
}
```

---

## Testing

The test suite uses pytest with `asyncio_mode = auto`. Repository tests run against a real in-memory SQLite instance. HTTP client interactions are mocked.

Run all tests:

```bash
pytest
```

On Windows:

```powershell
.venv\Scripts\pytest.exe
```

Additional options:

```bash
# Verbose output with test names
pytest -v

# Stop after the first failure
pytest -x

# Run a specific file
pytest tests/services/test_stock_service.py

# Run a specific test by name
pytest tests/services/test_stock_service.py::test_get_stock_summary
```

No `.env` file is required to run tests — `conftest.py` seeds `POLYGON_API_KEY` with a dummy value automatically.

---

## Linting and Formatting

The project uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting, configured in `pyproject.toml`.

```bash
# Check for issues
ruff check app/ tests/

# Auto-fix safe issues
ruff check app/ tests/ --fix

# Format code
ruff format app/ tests/
```

On Windows:

```powershell
.venv\Scripts\ruff.exe check app/ tests/
.venv\Scripts\ruff.exe check app/ tests/ --fix
.venv\Scripts\ruff.exe format app/ tests/
```

Enabled rule sets: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `ASYNC` (flake8-async), `B` (flake8-bugbear), `C4` (flake8-comprehensions), `SIM` (flake8-simplify).

Rule `B008` is suppressed intentionally — `Depends()` in default argument position is the standard FastAPI dependency injection pattern.

---

## Project Structure

```
dandb/
├── app/
│   ├── main.py                          # App factory, lifespan, exception handlers, /health
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings — all environment variables
│   │   └── clients/
│   │       ├── http_client.py           # BaseHTTPClient with retry/backoff (3 attempts)
│   │       ├── polygon_client.py        # Polygon.io OHLC client, anyio LRU cache
│   │       └── scraper.py               # MarketWatch HTML scraper, BeautifulSoup
│   ├── api/
│   │   └── v1/
│   │       ├── api.py                   # Router composition
│   │       ├── deps.py                  # All Depends() functions
│   │       ├── mappers.py               # Domain → Pydantic response translation
│   │       └── endpoints/
│   │           └── stocks.py            # GET /stock/{symbol}, POST /stock/{symbol}
│   ├── services/
│   │   └── stock_service.py             # Business logic, asyncio.gather for parallel I/O
│   ├── repositories/
│   │   └── holdings_repository.py       # SQLAlchemy async; upsert, increment, decrement
│   ├── models/
│   │   └── models.py                    # SQLAlchemy ORM model (UserStock)
│   └── schemas/
│       ├── domain_schema.py             # Frozen dataclasses (no framework dependencies)
│       └── stock_schemas.py             # Pydantic request/response models
├── tests/
│   ├── conftest.py                      # Seeds POLYGON_API_KEY for all tests
│   ├── api/v1/
│   │   ├── test_stocks.py               # Endpoint integration tests
│   │   └── test_deps.py                 # Dependency wiring tests
│   ├── services/
│   │   └── test_stock_service.py        # Service unit tests
│   └── repositories/
│       └── test_holdings_repository.py  # Repository tests (in-memory SQLite)
├── Dockerfile                           # Multi-stage build (builder + runtime)
├── entrypoint.sh                        # Docker entrypoint: privilege drop to appuser
├── pyproject.toml                       # Ruff configuration
├── pytest.ini                           # asyncio_mode = auto
├── requirements.txt                     # Runtime dependencies
└── .env                                 # Local environment variables (not committed)
```

---

## Docker

A multi-stage Dockerfile is included. The builder stage installs dependencies; the runtime stage copies only the installed packages and application code, runs as a non-root user (`appuser`), and mounts `/data` as a volume for the SQLite database file.

**Build:**

```bash
docker build -t dandb .
```

**Run:**

```bash
docker run -p 8000:8000 \
  -e POLYGON_API_KEY=your_key_here \
  -v "$(pwd)/data:/data" \
  dandb
```

`DATABASE_URL` is pre-set in the image to `/data/sql_app.db`. The SQLite file persists through the mounted volume and is owned by `appuser` — the container never runs as root.
