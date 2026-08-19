from typing import TYPE_CHECKING, Self

from psycopg import errors as psycopg_errors
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.music_catalog.application.errors import UniqueConstraintViolation
from roots_of_rhythm.music_catalog.infrastructure.assignment_repository import (
    SqlAlchemyClassificationAssignmentRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
)
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.music_catalog.application.ports import ClassificationAssignmentRepository, GenreRepository


class SqlAlchemyMusicCatalogUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session = session_factory()
        self.genres: GenreRepository = SqlAlchemyGenreRepository(self._session)
        self.assignments: ClassificationAssignmentRepository = SqlAlchemyClassificationAssignmentRepository(
            self._session
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
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
