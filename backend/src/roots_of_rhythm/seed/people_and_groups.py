"""People, groups, memberships, and their genre assignments."""

from typing import TYPE_CHECKING, cast
from uuid import UUID

from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransaction, SqlAlchemyTransactionScope
from roots_of_rhythm.music_catalog.application import (
    ClassificationAssignmentService,
    GroupMembershipService,
    GroupService,
    PublishClassificationAssignment,
)
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.domain import (
    ExistencePeriod,
    GroupContent,
    GroupMembershipContent,
)
from roots_of_rhythm.music_catalog.domain import TemporalBound as MusicTemporalBound
from roots_of_rhythm.music_catalog.domain import TemporalPrecision as MusicTemporalPrecision
from roots_of_rhythm.music_catalog.infrastructure.assignment_repository import (
    SqlAlchemyClassificationAssignmentRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.group_repository import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.domain import PersonContent
from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork
from roots_of_rhythm.seed.genre_knowledge import JAZZ_ID, JUMP_BLUES_ID, SWING_ID

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.transaction import Transaction
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork


def _session(transaction: "Transaction") -> "AsyncSession":
    return cast("SqlAlchemyTransaction", transaction).session


# --- Performers -------------------------------------------------------------
CHARLIE_PARKER_ID = UUID("01a01a72-1be4-763d-8892-9d922967d97d")
COUNT_BASIE_ID = UUID("01a01a72-1be5-7542-b935-47f2b3e1b5a3")
BENNY_GOODMAN_ID = UUID("01a01a72-1be5-7542-b935-47f33d83c2ab")
LOUIS_JORDAN_ID = UUID("01a01a72-1be5-7542-b935-47f4d3a8b6a4")
BIG_JOE_TURNER_ID = UUID("01a01a72-1be5-7542-b935-47f5372c5a61")
LOUIS_ARMSTRONG_ID = UUID("01a01a72-1be5-7542-b935-47f617f2cfd3")
MARIAN_ANDERSON_ID = UUID("01a01a72-1be5-7542-b935-47f617f2cfd4")

CHARLIE_PARKER_JAZZ_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47f73650f305")
COUNT_BASIE_SWING_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47f8242e6fb0")
BENNY_GOODMAN_SWING_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47f9f7082a27")
LOUIS_JORDAN_JUMP_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47faef4ad12c")
BIG_JOE_TURNER_JUMP_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47fb7216332d")
LOUIS_ARMSTRONG_JAZZ_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47fc9c2d6f8d")
LOUIS_ARMSTRONG_SWING_ASSIGNMENT_ID = UUID("01a01a72-1be5-7542-b935-47fd2ab545c0")

SEED_PERFORMERS: tuple[tuple[UUID, str], ...] = (
    (CHARLIE_PARKER_ID, "Charlie Parker"),
    (COUNT_BASIE_ID, "Count Basie"),
    (BENNY_GOODMAN_ID, "Benny Goodman"),
    (LOUIS_JORDAN_ID, "Louis Jordan"),
    (BIG_JOE_TURNER_ID, "Big Joe Turner"),
    (LOUIS_ARMSTRONG_ID, "Louis Armstrong"),
    (MARIAN_ANDERSON_ID, "Marian Anderson"),
)

SEED_ASSIGNMENT_PROVENANCE = "Controlled corpus editorial seed."
SEED_PERSON_GENRE_ASSIGNMENTS: tuple[tuple[UUID, UUID, UUID, str, str], ...] = (
    (
        CHARLIE_PARKER_JAZZ_ASSIGNMENT_ID,
        CHARLIE_PARKER_ID,
        JAZZ_ID,
        "Charlie Parker is classified as a Jazz performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        COUNT_BASIE_SWING_ASSIGNMENT_ID,
        COUNT_BASIE_ID,
        SWING_ID,
        "Count Basie is classified as a Swing performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        BENNY_GOODMAN_SWING_ASSIGNMENT_ID,
        BENNY_GOODMAN_ID,
        SWING_ID,
        "Benny Goodman is classified as a Swing performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        LOUIS_JORDAN_JUMP_ASSIGNMENT_ID,
        LOUIS_JORDAN_ID,
        JUMP_BLUES_ID,
        "Louis Jordan is classified as a Jump Blues performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        BIG_JOE_TURNER_JUMP_ASSIGNMENT_ID,
        BIG_JOE_TURNER_ID,
        JUMP_BLUES_ID,
        "Big Joe Turner is classified as a Jump Blues performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        LOUIS_ARMSTRONG_JAZZ_ASSIGNMENT_ID,
        LOUIS_ARMSTRONG_ID,
        JAZZ_ID,
        "Louis Armstrong is classified as a Jazz performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        LOUIS_ARMSTRONG_SWING_ASSIGNMENT_ID,
        LOUIS_ARMSTRONG_ID,
        SWING_ID,
        "Louis Armstrong is classified as a Swing performer.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
)

# --- Groups ---------------------------------------------------------------
BENNY_GOODMAN_ORCHESTRA_ID = UUID("01a01a72-2c01-7000-8000-000000000001")
CHARLIE_PARKER_QUINTET_ID = UUID("01a01a72-2c01-7000-8000-000000000002")
COUNT_BASIE_ORCHESTRA_ID = UUID("01a01a72-2c01-7000-8000-000000000003")
TYMPANY_FIVE_ID = UUID("01a01a72-2c01-7000-8000-000000000004")

CHARLIE_PARKER_QUINTET_MEMBERSHIP_ID = UUID("01a01a72-2c01-7000-8000-000000000011")
COUNT_BASIE_ORCHESTRA_MEMBERSHIP_ID = UUID("01a01a72-2c01-7000-8000-000000000012")
BENNY_GOODMAN_ORCHESTRA_MEMBERSHIP_ID = UUID("01a01a72-2c01-7000-8000-000000000013")
TYMPANY_FIVE_MEMBERSHIP_ID = UUID("01a01a72-2c01-7000-8000-000000000014")

CHARLIE_PARKER_QUINTET_JAZZ_ASSIGNMENT_ID = UUID("01a01a72-2c01-7000-8000-000000000021")
COUNT_BASIE_ORCHESTRA_SWING_ASSIGNMENT_ID = UUID("01a01a72-2c01-7000-8000-000000000022")
BENNY_GOODMAN_ORCHESTRA_SWING_ASSIGNMENT_ID = UUID("01a01a72-2c01-7000-8000-000000000023")
TYMPANY_FIVE_JUMP_ASSIGNMENT_ID = UUID("01a01a72-2c01-7000-8000-000000000024")

SEED_GROUPS: tuple[tuple[UUID, GroupContent], ...] = (
    (CHARLIE_PARKER_QUINTET_ID, GroupContent.create("Charlie Parker Quintet")),
    (COUNT_BASIE_ORCHESTRA_ID, GroupContent.create("Count Basie Orchestra")),
    (BENNY_GOODMAN_ORCHESTRA_ID, GroupContent.create("Benny Goodman Orchestra")),
    (TYMPANY_FIVE_ID, GroupContent.create("Tympany Five")),
)

SEED_GROUP_MEMBERSHIPS: tuple[tuple[UUID, UUID, UUID, GroupMembershipContent], ...] = (
    (
        CHARLIE_PARKER_QUINTET_MEMBERSHIP_ID,
        CHARLIE_PARKER_ID,
        CHARLIE_PARKER_QUINTET_ID,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(
                start=MusicTemporalBound(1945, MusicTemporalPrecision.EXACT_YEAR),
                end=MusicTemporalBound(1948, MusicTemporalPrecision.EXACT_YEAR),
            ),
            roles_or_instruments=("alto saxophone", "leader"),
        ),
    ),
    (
        COUNT_BASIE_ORCHESTRA_MEMBERSHIP_ID,
        COUNT_BASIE_ID,
        COUNT_BASIE_ORCHESTRA_ID,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(
                start=MusicTemporalBound(1935, MusicTemporalPrecision.EXACT_YEAR),
                end=MusicTemporalBound(1950, MusicTemporalPrecision.CIRCA_YEAR),
            ),
            roles_or_instruments=("piano", "bandleader"),
        ),
    ),
    (
        BENNY_GOODMAN_ORCHESTRA_MEMBERSHIP_ID,
        BENNY_GOODMAN_ID,
        BENNY_GOODMAN_ORCHESTRA_ID,
        GroupMembershipContent.create(roles_or_instruments=("clarinet",)),
    ),
    (
        TYMPANY_FIVE_MEMBERSHIP_ID,
        LOUIS_JORDAN_ID,
        TYMPANY_FIVE_ID,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(start=MusicTemporalBound(1941, MusicTemporalPrecision.EXACT_YEAR)),
            roles_or_instruments=("vocals", "saxophone"),
        ),
    ),
)

SEED_GROUP_GENRE_ASSIGNMENTS: tuple[tuple[UUID, UUID, UUID, str, str], ...] = (
    (
        CHARLIE_PARKER_QUINTET_JAZZ_ASSIGNMENT_ID,
        CHARLIE_PARKER_QUINTET_ID,
        JAZZ_ID,
        "Charlie Parker Quintet is classified as a Jazz group.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        COUNT_BASIE_ORCHESTRA_SWING_ASSIGNMENT_ID,
        COUNT_BASIE_ORCHESTRA_ID,
        SWING_ID,
        "Count Basie Orchestra is classified as a Swing group.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        BENNY_GOODMAN_ORCHESTRA_SWING_ASSIGNMENT_ID,
        BENNY_GOODMAN_ORCHESTRA_ID,
        SWING_ID,
        "Benny Goodman Orchestra is classified as a Swing group.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
    (
        TYMPANY_FIVE_JUMP_ASSIGNMENT_ID,
        TYMPANY_FIVE_ID,
        JUMP_BLUES_ID,
        "Tympany Five is classified as a Jump Blues group.",
        SEED_ASSIGNMENT_PROVENANCE,
    ),
)

# --- Song authors (WorkCredit only; performers are RecordingCredit in STORY-008) ---
MERLE_TRAVIS_ID = UUID("01a01a72-3b01-7000-8000-000000000001")
LOUIS_PRIMA_ID = UUID("01a01a72-3b01-7000-8000-000000000002")
JESSE_STONE_ID = UUID("01a01a72-3b01-7000-8000-000000000003")
KING_OLIVER_ID = UUID("01a01a72-3b01-7000-8000-000000000004")

SEED_SONG_AUTHORS: tuple[tuple[UUID, str], ...] = (
    (MERLE_TRAVIS_ID, "Merle Travis"),
    (LOUIS_PRIMA_ID, "Louis Prima"),
    (JESSE_STONE_ID, "Jesse Stone"),
    (KING_OLIVER_ID, "King Oliver"),
)

TENNESSEE_ERNIE_FORD_ID = UUID("01a01a72-3b01-7000-8000-000000000005")
STEVIE_WONDER_ID = UUID("01a01a72-3b01-7000-8000-000000000006")
SEED_RECORDING_PERFORMERS: tuple[tuple[UUID, str], ...] = (
    (TENNESSEE_ERNIE_FORD_ID, "Tennessee Ernie Ford"),
    (STEVIE_WONDER_ID, "Stevie Wonder"),
)


class PeopleAndGroupsSeed:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._music_uow: Callable[[], SqlAlchemyMusicCatalogUnitOfWork] = lambda: SqlAlchemyMusicCatalogUnitOfWork(
            session_factory
        )
        self._people_uow: Callable[[], PeopleCatalogUnitOfWork] = lambda: SqlAlchemyPeopleCatalogUnitOfWork(
            session_factory
        )
        self._persons = PersonService(self._people_uow)
        self._groups = GroupService(self._music_uow)
        self._group_memberships = GroupMembershipService(self._music_uow)
        transaction_scope = SqlAlchemyTransactionScope(session_factory)

        def assignment_repository(transaction: "Transaction") -> SqlAlchemyClassificationAssignmentRepository:
            return SqlAlchemyClassificationAssignmentRepository(_session(transaction))

        self._assignments = ClassificationAssignmentService(transaction_scope, assignment_repository)
        self._publish_assignment = PublishClassificationAssignment(
            transaction_scope,
            assignment_repository,
            lambda transaction: SqlAlchemyGenreRepository(_session(transaction)),
            lambda transaction: SqlAlchemyGroupRepository(_session(transaction)),
            lambda transaction: SqlAlchemyPersonRepository(_session(transaction)),
        )

    async def run(self) -> None:
        await self._ensure_persons()
        await self._ensure_groups()
        await self._ensure_group_memberships()
        await self._ensure_assignments()
        await self._ensure_group_genre_assignments()

    async def _ensure_persons(self) -> None:
        for person_id, name in (
            *SEED_PERFORMERS,
            *SEED_SONG_AUTHORS,
            *SEED_RECORDING_PERFORMERS,
        ):
            await self._ensure_published_person(person_id, name)

    async def _ensure_published_person(self, person_id: UUID, name: str) -> None:
        async with self._people_uow() as uow:
            existing = await uow.persons.get(person_id)
        if existing is None:
            await self._persons.create(PersonContent.create(name), person_id=person_id)
            await self._persons.publish(person_id)
            return
        if existing.editorial_status is not PersonEditorialStatus.PUBLISHED:
            await self._persons.publish(person_id)

    async def _ensure_assignments(self) -> None:
        for assignment_id, person_id, genre_id, explanation, provenance in SEED_PERSON_GENRE_ASSIGNMENTS:
            await self._ensure_published_person_assignment(
                assignment_id,
                person_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
            )

    async def _ensure_group_genre_assignments(self) -> None:
        for assignment_id, group_id, genre_id, explanation, provenance in SEED_GROUP_GENRE_ASSIGNMENTS:
            await self._ensure_published_group_assignment(
                assignment_id,
                group_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
            )

    async def _ensure_groups(self) -> None:
        for group_id, content in SEED_GROUPS:
            await self._ensure_published_group(group_id, content)

    async def _ensure_published_group(self, group_id: UUID, content: GroupContent) -> None:
        async with self._music_uow() as uow:
            existing = await uow.groups.get(group_id)
        if existing is None:
            await self._groups.create(content, group_id=group_id)
            await self._groups.publish(group_id)
            return
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._groups.publish(group_id)

    async def _ensure_group_memberships(self) -> None:
        for membership_id, person_id, group_id, content in SEED_GROUP_MEMBERSHIPS:
            await self._ensure_published_group_membership(membership_id, person_id, group_id, content)

    async def _ensure_published_group_membership(
        self,
        membership_id: UUID,
        person_id: UUID,
        group_id: UUID,
        content: GroupMembershipContent,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.group_memberships.get(membership_id)
        if existing is None:
            await self._group_memberships.create(person_id, group_id, content, membership_id=membership_id)
            await self._group_memberships.publish(membership_id)
            return
        if (
            existing.period != content.period
            or existing.roles_or_instruments != content.roles_or_instruments
            or existing.provenance != content.provenance
        ):
            await self._group_memberships.replace_content(membership_id, content)
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._group_memberships.publish(membership_id)

    async def _ensure_published_person_assignment(
        self,
        assignment_id: UUID,
        person_id: UUID,
        genre_id: UUID,
        *,
        explanation: str,
        provenance: str,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.assignments.get(assignment_id)
        if existing is None:
            await self._assignments.create_for_person(
                person_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
                assignment_id=assignment_id,
            )
            await self._publish_assignment.execute(assignment_id)
            return
        if existing.explanation != explanation or existing.provenance != provenance:
            await self._assignments.replace_content(
                assignment_id,
                explanation=explanation,
                claim_id=existing.claim_id,
                provenance=provenance,
                evidence_status=existing.evidence_status,
            )
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._publish_assignment.execute(assignment_id)

    async def _ensure_published_group_assignment(
        self,
        assignment_id: UUID,
        group_id: UUID,
        genre_id: UUID,
        *,
        explanation: str,
        provenance: str,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.assignments.get(assignment_id)
        if existing is None:
            await self._assignments.create_for_group(
                group_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
                assignment_id=assignment_id,
            )
            await self._publish_assignment.execute(assignment_id)
            return
        if existing.explanation != explanation or existing.provenance != provenance:
            await self._assignments.replace_content(
                assignment_id,
                explanation=explanation,
                claim_id=existing.claim_id,
                provenance=provenance,
                evidence_status=existing.evidence_status,
            )
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._publish_assignment.execute(assignment_id)
