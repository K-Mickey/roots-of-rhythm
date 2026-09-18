from typing import TYPE_CHECKING, Self

from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.music_catalog.infrastructure.repositories.assignment import (
    SqlAlchemyClassificationAssignmentRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.repositories.genre import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.group import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.group_membership import (
    SqlAlchemyGroupMembershipRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.repositories.lyrics_version import SqlAlchemyLyricsVersionRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.lyrics_version_credit import (
    SqlAlchemyLyricsVersionCreditRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.repositories.lyrics_version_relation import (
    SqlAlchemyLyricsVersionRelationRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.repositories.musical_work import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.recording import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.work_credit import SqlAlchemyWorkCreditRepository
from roots_of_rhythm.music_catalog.infrastructure.repositories.work_relation import SqlAlchemyWorkRelationRepository

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
        except IntegrityError:
            await self.rollback()
            raise

    async def rollback(self) -> None:
        await self._session.rollback()
