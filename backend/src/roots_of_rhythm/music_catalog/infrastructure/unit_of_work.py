from typing import TYPE_CHECKING, Self

from psycopg import errors as psycopg_errors
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.music_catalog.application.errors import UniqueConstraintViolation
from roots_of_rhythm.music_catalog.infrastructure.assignment_repository import (
    SqlAlchemyClassificationAssignmentRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.group_membership_repository import (
    SqlAlchemyGroupMembershipRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.group_repository import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
)
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.music_catalog.application.ports import (
        ClassificationAssignmentRepository,
        GenreRepository,
        GroupMembershipRepository,
        GroupRepository,
    )


class SqlAlchemyMusicCatalogUnitOfWork:
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
        self.genres: GenreRepository = SqlAlchemyGenreRepository(session)
        self.assignments: ClassificationAssignmentRepository = SqlAlchemyClassificationAssignmentRepository(session)
        self.groups: GroupRepository = SqlAlchemyGroupRepository(session)
        self.group_memberships: GroupMembershipRepository = SqlAlchemyGroupMembershipRepository(session)

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
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self.rollback()
            name = _constraint_name(error)
            if name in {
                CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
                CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
            }:
                raise UniqueConstraintViolation(name) from error
            raise

    async def rollback(self) -> None:
        await self._session.rollback()


def _constraint_name(error: IntegrityError) -> str | None:
    if isinstance(error.orig, psycopg_errors.UniqueViolation):
        return error.orig.diag.constraint_name
    return None
