import pytest
import pytest_asyncio
from holdings_repository import StockHoldingsRepository


@pytest_asyncio.fixture
async def repo():
    return await StockHoldingsRepository.create(":memory:")


class TestUpsert:

    async def test_insert_new_symbol(self, repo):
        await repo.upsert("AAPL", 10)
        assert await repo.get("AAPL") == 10

    async def test_upsert_existing_symbol_replaces_amount(self, repo):
        await repo.upsert("AAPL", 10)
        await repo.upsert("AAPL", 25)
        assert await repo.get("AAPL") == 25


class TestAddAmount:

    async def test_add_to_new_symbol_creates_row(self, repo):
        await repo.add_amount("TSLA", 5)
        assert await repo.get("TSLA") == 5

    async def test_add_to_existing_symbol_increments(self, repo):
        await repo.upsert("TSLA", 10)
        await repo.add_amount("TSLA", 5)
        assert await repo.get("TSLA") == 15


class TestGet:

    async def test_get_existing_symbol_returns_amount(self, repo):
        await repo.upsert("MSFT", 7)
        assert await repo.get("MSFT") == 7

    async def test_get_missing_symbol_returns_none(self, repo):
        assert await repo.get("MISSING") is None


class TestGetAll:

    async def test_empty_db_returns_empty_list(self, repo):
        assert await repo.get_all() == []

    async def test_multiple_rows_returns_all(self, repo):
        await repo.upsert("AAPL", 10)
        await repo.upsert("MSFT", 20)
        result = await repo.get_all()
        assert sorted(result) == [("AAPL", 10), ("MSFT", 20)]


class TestDelete:

    async def test_delete_existing_symbol_returns_true_and_removes_row(self, repo):
        await repo.upsert("GOOG", 3)
        assert await repo.delete("GOOG") is True
        assert await repo.get("GOOG") is None

    async def test_delete_missing_symbol_returns_false(self, repo):
        assert await repo.delete("MISSING") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
