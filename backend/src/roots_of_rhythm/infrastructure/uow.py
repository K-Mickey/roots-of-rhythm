from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor


class PgUnitOfWork:
    def __init__(self, pg: PgAccessor) -> None:
        self._pg = pg

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[None]:
        if self._pg.in_child_task():
            raise RuntimeError(
                "PgUnitOfWork entered from an asyncio child task of the pg request scope; "
                "run write operations in the main request task"
            )
        if self._pg.get_current_session() is not None:
            yield
            return
        async with self._pg.new_session():
            yield
