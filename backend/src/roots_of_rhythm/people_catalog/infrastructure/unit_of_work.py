from typing import TYPE_CHECKING, Self

from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.people_catalog.application.ports import PersonRepository


class SqlAlchemyPeopleCatalogUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._bind(session_factory(), owns_session=True)

    @classmethod
    def using(cls, session: AsyncSession) -> Self:
        instance = cls.__new__(cls)
        instance._bind(session, owns_session=False)
        return instance

    def _bind(self, session: AsyncSession, *, owns_session: bool) -> None:
        self._session = session
        self._owns_session = owns_session
        self.persons: PersonRepository = SqlAlchemyPersonRepository(session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._owns_session:
            return
        await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
