import pytest

from app.repositories.holdings_repository import (
    InsufficientFundsException,
    StockHoldingsRepository,
)


@pytest.fixture
async def repo() -> StockHoldingsRepository:
    return await StockHoldingsRepository.create(":memory:")


async def test_upsert_inserts_new_symbol(repo):
    await repo._set_holding("AAPL", 10)
    assert await repo.get("AAPL") == 10


async def test_upsert_replaces_amount_for_existing_symbol(repo):
    await repo._set_holding("AAPL", 10)
    await repo._set_holding("AAPL", 5)
    assert await repo.get("AAPL") == 5


async def test_update_balance_inserts_new_symbol(repo):
    await repo.update_holding("AAPL", 7)
    assert await repo.get("AAPL") == 7


async def test_update_balance_accumulates_for_existing_symbol(repo):
    await repo.update_holding("AAPL", 10)
    await repo.update_holding("AAPL", 5)
    assert await repo.get("AAPL") == 15


async def test_get_returns_none_for_unknown_symbol(repo):
    assert await repo.get("UNKNOWN") is None


async def test_delete_removes_existing_symbol(repo):
    await repo.update_holding("AAPL", 10)
    deleted = await repo._delete("AAPL")
    assert deleted is True
    assert await repo.get("AAPL") is None


async def test_delete_returns_false_for_unknown_symbol(repo):
    result = await repo._delete("UNKNOWN")
    assert result is False


async def test_update_holding_subtracts_shares(repo):
    await repo.update_holding("AAPL", 10)
    await repo.update_holding("AAPL", -3)
    assert await repo.get("AAPL") == 7


async def test_subtract_shares_raises_insufficient_funds(repo):
    await repo.update_holding("AAPL", 5)
    with pytest.raises(InsufficientFundsException) as exc_info:
        await repo.update_holding("AAPL", -10)
    assert exc_info.value.symbol == "AAPL"


async def test_context_manager_aexit_disposes_engine():
    from unittest.mock import AsyncMock, MagicMock

    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    repo = StockHoldingsRepository(mock_engine)
    async with repo:
        pass
    mock_engine.dispose.assert_called_once()
