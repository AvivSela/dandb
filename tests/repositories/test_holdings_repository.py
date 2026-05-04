import pytest

from app.repositories.holdings_repository import StockHoldingsRepository


@pytest.fixture
async def repo() -> StockHoldingsRepository:
    return await StockHoldingsRepository.create(":memory:")


async def test_upsert_inserts_new_symbol(repo):
    await repo._upsert("AAPL", 10)
    assert await repo.get("AAPL") == 10


async def test_upsert_replaces_amount_for_existing_symbol(repo):
    await repo._upsert("AAPL", 10)
    await repo._upsert("AAPL", 5)
    assert await repo.get("AAPL") == 5


async def test_update_balance_inserts_new_symbol(repo):
    await repo.update_balance("AAPL", 7)
    assert await repo.get("AAPL") == 7


async def test_update_balance_accumulates_for_existing_symbol(repo):
    await repo.update_balance("AAPL", 10)
    await repo.update_balance("AAPL", 5)
    assert await repo.get("AAPL") == 15


async def test_get_returns_none_for_unknown_symbol(repo):
    assert await repo.get("UNKNOWN") is None


async def test_delete_removes_existing_symbol(repo):
    await repo.update_balance("AAPL", 10)
    deleted = await repo._delete("AAPL")
    assert deleted is True
    assert await repo.get("AAPL") is None


async def test_delete_returns_false_for_unknown_symbol(repo):
    result = await repo._delete("UNKNOWN")
    assert result is False
