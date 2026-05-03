# dandb

FastAPI service aggregating stock market data from Polygon.io and MarketWatch.

## Setup

Create a `.env` file in the project root:

```
POLYGON_API_KEY=<your_key>
```

Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite httpx pydantic pydantic-settings \
            python-dotenv beautifulsoup4 pytest pytest-asyncio anyio ruff
```

## Run

```bash
uvicorn app.main:app --reload
```

## Lint & Format (ruff)

```bash
# Check for issues
.venv\Scripts\ruff.exe check app/ tests/

# Auto-fix safe issues
.venv\Scripts\ruff.exe check app/ tests/ --fix

# Format code
.venv\Scripts\ruff.exe format app/ tests/
```

## Tests

```bash
pytest
```
