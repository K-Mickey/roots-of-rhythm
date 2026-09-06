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
    @asynccontextmanager
    async def scope() -> AsyncIterator[Transaction]:
        yield FakeTransaction()

    return scope
