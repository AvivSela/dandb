# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Non-root user + writable data dir
RUN groupadd --system appgroup \
 && useradd --system --gid appgroup --no-create-home appuser \
 && mkdir -p /data && chown appuser:appgroup /data

WORKDIR /app

COPY --chown=appuser:appgroup app/ ./app/

USER appuser

ENV DATABASE_URL=sqlite+aiosqlite:////data/sql_app.db

VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
