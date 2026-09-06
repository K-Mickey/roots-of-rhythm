from typing import TYPE_CHECKING, Self

from tests.music_catalog.fakes.assignments import FakeClassificationAssignmentRepository
from tests.music_catalog.fakes.genres import FakeGenreRepository
from tests.music_catalog.fakes.groups import FakeGroupMembershipRepository, FakeGroupRepository
from tests.music_catalog.fakes.lyrics import (
    FakeLyricsVersionCreditRepository,
    FakeLyricsVersionRelationRepository,
    FakeLyricsVersionRepository,
)
from tests.music_catalog.fakes.works import (
    FakeMusicalWorkRepository,
    FakeWorkCreditRepository,
    FakeWorkRelationRepository,
)

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import (
        ClassificationAssignmentRepository,
        GenreRepository,
        GroupMembershipRepository,
        GroupRepository,
        LyricsVersionCreditRepository,
        LyricsVersionRelationRepository,
        LyricsVersionRepository,
        MusicalWorkRepository,
        WorkCreditRepository,
        WorkRelationRepository,
    )
    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        GroupMembership,
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
        MusicalWork,
        WorkCredit,
        WorkRelation,
    )


class FakeMusicCatalogUnitOfWork:
    def __init__(
        self,
        genres: dict[UUID, Genre],
        assignments: dict[UUID, ClassificationAssignment] | None = None,
        groups: dict[UUID, Group] | None = None,
        group_memberships: dict[UUID, GroupMembership] | None = None,
        works: dict[UUID, MusicalWork] | None = None,
        work_credits: dict[UUID, WorkCredit] | None = None,
        work_relations: dict[UUID, WorkRelation] | None = None,
        lyrics_versions: dict[UUID, LyricsVersion] | None = None,
        lyrics_version_credits: dict[UUID, LyricsVersionCredit] | None = None,
        lyrics_version_relations: dict[UUID, LyricsVersionRelation] | None = None,
    ) -> None:
        self.genres: GenreRepository = FakeGenreRepository(genres)
        self.assignments: ClassificationAssignmentRepository = FakeClassificationAssignmentRepository(
            {} if assignments is None else assignments
        )
        self.groups: GroupRepository = FakeGroupRepository({} if groups is None else groups)
        self.group_memberships: GroupMembershipRepository = FakeGroupMembershipRepository(
            {} if group_memberships is None else group_memberships
        )
        self.works: MusicalWorkRepository = FakeMusicalWorkRepository({} if works is None else works)
        self.work_credits: WorkCreditRepository = FakeWorkCreditRepository({} if work_credits is None else work_credits)
        self.work_relations: WorkRelationRepository = FakeWorkRelationRepository(
            {} if work_relations is None else work_relations
        )
        self.lyrics_versions: LyricsVersionRepository = FakeLyricsVersionRepository(
            {} if lyrics_versions is None else lyrics_versions
        )
        self.lyrics_version_credits: LyricsVersionCreditRepository = FakeLyricsVersionCreditRepository(
            {} if lyrics_version_credits is None else lyrics_version_credits
        )
        self.lyrics_version_relations: LyricsVersionRelationRepository = FakeLyricsVersionRelationRepository(
            {} if lyrics_version_relations is None else lyrics_version_relations
        )
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
