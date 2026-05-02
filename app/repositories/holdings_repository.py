from sqlalchemy import delete, select, event
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.models import Base, UserStock


class StockHoldingsRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    async def create(cls, db_path: str = "user_stocks.db") -> "StockHoldingsRepository":
        if db_path == ":memory:":
            engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            engine = create_async_engine(
                f"sqlite+aiosqlite:///{db_path}",
                connect_args={"check_same_thread": False},
            )

            @event.listens_for(engine.sync_engine, "connect")
            def _set_wal(dbapi_conn, _):
                dbapi_conn.execute("PRAGMA journal_mode=WAL")

        repo = cls(engine)
        await repo._init_db()
        return repo

    async def _init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def upsert(self, symbol: str, amount: int) -> None:
        stmt = (
            sqlite_insert(UserStock)
            .values(stock_symbol=symbol, amount=amount)
            .on_conflict_do_update(index_elements=["stock_symbol"], set_={"amount": amount})
        )
        async with self._session_factory.begin() as session:
            await session.execute(stmt)

    async def add_amount(self, symbol: str, amount: int) -> None:
        stmt = (
            sqlite_insert(UserStock)
            .values(stock_symbol=symbol, amount=amount)
            .on_conflict_do_update(
                index_elements=["stock_symbol"],
                set_={"amount": UserStock.amount + amount},
            )
        )
        async with self._session_factory.begin() as session:
            await session.execute(stmt)

    async def get(self, symbol: str) -> int | None:
        stmt = select(UserStock.amount).where(UserStock.stock_symbol == symbol)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[tuple[str, int]]:
        stmt = select(UserStock.stock_symbol, UserStock.amount)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
        return [(r.stock_symbol, r.amount) for r in result.all()]

    async def delete(self, symbol: str) -> bool:
        # Adding .returning ensures we get the symbol back if it existed
        stmt = delete(UserStock).where(UserStock.stock_symbol == symbol).returning(UserStock.stock_symbol)
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(stmt)
                # .scalar() returns the first column of the first row, or None
                deleted_symbol = result.scalar()
                return deleted_symbol is not None