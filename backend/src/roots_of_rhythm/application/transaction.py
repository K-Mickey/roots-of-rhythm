from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol


class Transaction(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


type TransactionScopeFactory = Callable[[], AbstractAsyncContextManager[Transaction]]
