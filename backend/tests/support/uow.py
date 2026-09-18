from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class FakeUnitOfWork:
    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[None]:
        yield
