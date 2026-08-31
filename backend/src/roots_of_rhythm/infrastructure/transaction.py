from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlAlchemyTransaction:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._rolled_back = False

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except BaseException:
            await self.rollback()
            raise

    async def rollback(self) -> None:
        if self._rolled_back:
            return
        await self.session.rollback()
        self._rolled_back = True


class SqlAlchemyTransactionScope:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[SqlAlchemyTransaction]:
        session = self._session_factory()
        transaction = SqlAlchemyTransaction(session)
        try:
            yield transaction
        except BaseException:
            await transaction.rollback()
            raise
        finally:
            await transaction.rollback()
            await session.close()
