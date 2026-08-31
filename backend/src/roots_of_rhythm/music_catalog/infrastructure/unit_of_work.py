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
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_credit_repository import (
    SqlAlchemyLyricsVersionCreditRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_relation_repository import (
    SqlAlchemyLyricsVersionRelationRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_repository import SqlAlchemyLyricsVersionRepository
from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
    LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT,
    LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT,
    LYRICS_VERSION_UNIQUE_CONSTRAINT,
    WORK_CREDIT_UNIQUE_CONSTRAINT,
    WORK_RELATION_UNIQUE_CONSTRAINT,
)
from roots_of_rhythm.music_catalog.infrastructure.musical_work_repository import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.work_credit_repository import SqlAlchemyWorkCreditRepository
from roots_of_rhythm.music_catalog.infrastructure.work_relation_repository import SqlAlchemyWorkRelationRepository

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.music_catalog.application.ports import (
        ClassificationAssignmentRepository,
        GenreRepository,
        GroupMembershipRepository,
        GroupRepository,
        LyricsVersionCreditRepository,
        LyricsVersionRelationRepository,
        LyricsVersionRepository,
        MusicalWorkRepository,
        RecordingRepository,
        WorkCreditRepository,
        WorkRelationRepository,
    )


class SqlAlchemyMusicCatalogUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session = session_factory()
        self.genres: GenreRepository = SqlAlchemyGenreRepository(self._session)
        self.assignments: ClassificationAssignmentRepository = SqlAlchemyClassificationAssignmentRepository(
            self._session
        )
        self.groups: GroupRepository = SqlAlchemyGroupRepository(self._session)
        self.group_memberships: GroupMembershipRepository = SqlAlchemyGroupMembershipRepository(self._session)
        self.works: MusicalWorkRepository = SqlAlchemyMusicalWorkRepository(self._session)
        self.work_credits: WorkCreditRepository = SqlAlchemyWorkCreditRepository(self._session)
        self.work_relations: WorkRelationRepository = SqlAlchemyWorkRelationRepository(self._session)
        self.lyrics_versions: LyricsVersionRepository = SqlAlchemyLyricsVersionRepository(self._session)
        self.lyrics_version_credits: LyricsVersionCreditRepository = SqlAlchemyLyricsVersionCreditRepository(
            self._session
        )
        self.lyrics_version_relations: LyricsVersionRelationRepository = SqlAlchemyLyricsVersionRelationRepository(
            self._session
        )
        self.recordings: RecordingRepository = SqlAlchemyRecordingRepository(self._session)

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

            name = None
            if isinstance(error.orig, psycopg_errors.UniqueViolation):
                name = error.orig.diag.constraint_name

            if name in {
                CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
                CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
                WORK_CREDIT_UNIQUE_CONSTRAINT,
                WORK_RELATION_UNIQUE_CONSTRAINT,
                LYRICS_VERSION_UNIQUE_CONSTRAINT,
                LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT,
                LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT,
            }:
                raise UniqueConstraintViolation(name) from error
            raise

    async def rollback(self) -> None:
        await self._session.rollback()
