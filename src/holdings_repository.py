import sqlite3
import uuid
import aiosqlite
from contextlib import asynccontextmanager


class StockHoldingsRepository:
    def __init__(self, db_path: str = "user_stocks.db"):
        if db_path == ":memory:":
            self._db_uri = f"file:memdb_{uuid.uuid4().hex}?mode=memory&cache=shared"
            self._use_uri = True
            self._anchor = sqlite3.connect(self._db_uri, uri=True)
        else:
            self._db_uri = db_path
            self._use_uri = False
            self._anchor = None

    @classmethod
    async def create(cls, db_path: str = "user_stocks.db") -> "StockHoldingsRepository":
        repo = cls(db_path)
        await repo._init_db()
        return repo

    async def _init_db(self):
        async with self._conn() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_stocks (
                    stock_symbol TEXT PRIMARY KEY,
                    amount       INTEGER NOT NULL
                )
                """
            )
            if not self._use_uri:
                await conn.execute("PRAGMA journal_mode=WAL")

    @asynccontextmanager
    async def _conn(self):
        async with aiosqlite.connect(self._db_uri, uri=self._use_uri) as conn:
            try:
                yield conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

    async def upsert(self, symbol: str, amount: int) -> None:
        async with self._conn() as conn:
            await conn.execute(
                "INSERT INTO user_stocks (stock_symbol, amount) VALUES (?, ?)"
                " ON CONFLICT(stock_symbol) DO UPDATE SET amount = excluded.amount",
                (symbol, amount),
            )

    async def add_amount(self, symbol: str, amount: int) -> None:
        async with self._conn() as conn:
            await conn.execute(
                "INSERT INTO user_stocks (stock_symbol, amount) VALUES (?, ?)"
                " ON CONFLICT(stock_symbol) DO UPDATE SET amount = amount + excluded.amount",
                (symbol, amount),
            )

    async def get(self, symbol: str) -> int | None:
        async with self._conn() as conn:
            cursor = await conn.execute(
                "SELECT amount FROM user_stocks WHERE stock_symbol = ?", (symbol,)
            )
            row = await cursor.fetchone()
        return row[0] if row else None

    async def get_all(self) -> list[tuple[str, int]]:
        async with self._conn() as conn:
            cursor = await conn.execute(
                "SELECT stock_symbol, amount FROM user_stocks"
            )
            rows = await cursor.fetchall()
        return rows

    async def delete(self, symbol: str) -> bool:
        async with self._conn() as conn:
            cursor = await conn.execute(
                "DELETE FROM user_stocks WHERE stock_symbol = ?", (symbol,)
            )
        return cursor.rowcount > 0
