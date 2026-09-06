from __future__ import annotations

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from roots_of_rhythm.application.transaction import Transaction


class FakeTransaction:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def fake_transaction_scope() -> Callable[[], AbstractAsyncContextManager[Transaction]]:
    return _build_scope(FakeTransaction)


class CountingTransaction:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


def counting_transaction_scope() -> tuple[
    Callable[[], AbstractAsyncContextManager[Transaction]],
    CountingTransaction,
]:
    shared = CountingTransaction()
    return _build_scope(lambda: shared), shared


def _build_scope(
    transaction_factory: Callable[[], Transaction],
) -> Callable[[], AbstractAsyncContextManager[Transaction]]:
    @asynccontextmanager
    async def scope() -> AsyncIterator[Transaction]:
        yield transaction_factory()

    return scope
