from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import AsyncIterator


class UnitOfWork(Protocol):
    """Границы транзакции: все операции внутри `async with uow()` выполняются атомарно."""

    @asynccontextmanager
    def __call__(self) -> AsyncIterator[None]: ...
