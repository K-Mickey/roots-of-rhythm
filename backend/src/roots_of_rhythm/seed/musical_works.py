"""Musical works and their author credits."""

from typing import TYPE_CHECKING
from uuid import UUID

from roots_of_rhythm.music_catalog.application import MusicalWorkService, WorkCreditService
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.domain import WorkContent, WorkCreditContent, WorkCreditRole
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.seed.people_and_groups import (
    CHARLIE_PARKER_ID,
    COUNT_BASIE_ID,
    JESSE_STONE_ID,
    KING_OLIVER_ID,
    LOUIS_PRIMA_ID,
    MERLE_TRAVIS_ID,
    SEED_ASSIGNMENT_PROVENANCE,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# --- Musical works ----------------------------------------------------------
SIXTEEN_TONS_ID = UUID("01a01a72-3c01-7000-8000-000000000001")
ONE_O_CLOCK_JUMP_ID = UUID("01a01a72-3c01-7000-8000-000000000002")
ORNITHOLOGY_ID = UUID("01a01a72-3c01-7000-8000-000000000003")
SING_SING_SING_ID = UUID("01a01a72-3c01-7000-8000-000000000004")
SHAKE_RATTLE_AND_ROLL_ID = UUID("01a01a72-3c01-7000-8000-000000000005")
WEST_END_BLUES_ID = UUID("01a01a72-3c01-7000-8000-000000000006")

SEED_WORK_PROVENANCE = SEED_ASSIGNMENT_PROVENANCE

SEED_MUSICAL_WORKS: tuple[tuple[UUID, WorkContent], ...] = (
    (
        SIXTEEN_TONS_ID,
        WorkContent.create("Sixteen Tons", provenance=SEED_WORK_PROVENANCE),
    ),
    (
        ONE_O_CLOCK_JUMP_ID,
        WorkContent.create("One O'Clock Jump", provenance=SEED_WORK_PROVENANCE),
    ),
    (
        ORNITHOLOGY_ID,
        WorkContent.create("Ornithology", provenance=SEED_WORK_PROVENANCE),
    ),
    (
        SING_SING_SING_ID,
        WorkContent.create("Sing, Sing, Sing (With a Swing)", provenance=SEED_WORK_PROVENANCE),
    ),
    (
        SHAKE_RATTLE_AND_ROLL_ID,
        WorkContent.create("Shake, Rattle and Roll", provenance=SEED_WORK_PROVENANCE),
    ),
    (
        WEST_END_BLUES_ID,
        WorkContent.create("West End Blues", provenance=SEED_WORK_PROVENANCE),
    ),
)

SIXTEEN_TONS_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000011")
SIXTEEN_TONS_LYRICIST_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000012")
ONE_O_CLOCK_JUMP_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000013")
ORNITHOLOGY_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000014")
SING_SING_SING_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000015")
SHAKE_RATTLE_AND_ROLL_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000016")
WEST_END_BLUES_COMPOSER_CREDIT_ID = UUID("01a01a72-3c01-7000-8000-000000000017")

# credit_id, work_id, person_id, role, credited_as
SEED_WORK_CREDITS: tuple[tuple[UUID, UUID, UUID, WorkCreditRole, str | None], ...] = (
    (
        SIXTEEN_TONS_COMPOSER_CREDIT_ID,
        SIXTEEN_TONS_ID,
        MERLE_TRAVIS_ID,
        WorkCreditRole.COMPOSER,
        None,
    ),
    (
        SIXTEEN_TONS_LYRICIST_CREDIT_ID,
        SIXTEEN_TONS_ID,
        MERLE_TRAVIS_ID,
        WorkCreditRole.LYRICIST,
        None,
    ),
    (
        ONE_O_CLOCK_JUMP_COMPOSER_CREDIT_ID,
        ONE_O_CLOCK_JUMP_ID,
        COUNT_BASIE_ID,
        WorkCreditRole.COMPOSER,
        None,
    ),
    (
        ORNITHOLOGY_COMPOSER_CREDIT_ID,
        ORNITHOLOGY_ID,
        CHARLIE_PARKER_ID,
        WorkCreditRole.COMPOSER,
        None,
    ),
    (
        SING_SING_SING_COMPOSER_CREDIT_ID,
        SING_SING_SING_ID,
        LOUIS_PRIMA_ID,
        WorkCreditRole.COMPOSER,
        None,
    ),
    (
        SHAKE_RATTLE_AND_ROLL_COMPOSER_CREDIT_ID,
        SHAKE_RATTLE_AND_ROLL_ID,
        JESSE_STONE_ID,
        WorkCreditRole.COMPOSER,
        "Charles Calhoun",
    ),
    (
        WEST_END_BLUES_COMPOSER_CREDIT_ID,
        WEST_END_BLUES_ID,
        KING_OLIVER_ID,
        WorkCreditRole.COMPOSER,
        None,
    ),
)


class MusicalWorksSeed:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._music_uow: Callable[[], SqlAlchemyMusicCatalogUnitOfWork] = lambda: SqlAlchemyMusicCatalogUnitOfWork(
            session_factory
        )
        self._works = MusicalWorkService(self._music_uow)
        self._work_credits = WorkCreditService(self._music_uow)

    async def run(self) -> None:
        await self._ensure_musical_works()
        await self._ensure_work_credits()

    async def _ensure_musical_works(self) -> None:
        for work_id, content in SEED_MUSICAL_WORKS:
            await self._ensure_published_work(work_id, content)

    async def _ensure_published_work(self, work_id: UUID, content: WorkContent) -> None:
        async with self._music_uow() as uow:
            existing = await uow.works.get(work_id)
        if existing is None:
            await self._works.create(content, work_id=work_id)
            await self._works.publish(work_id)
            return
        if (
            existing.canonical_title != content.canonical_title
            or existing.aliases != content.aliases
            or existing.description != content.description
            or existing.period != content.period
            or existing.external_identities != content.external_identities
            or existing.provenance != content.provenance
        ):
            await self._works.replace_content(work_id, content)
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._works.publish(work_id)

    async def _ensure_work_credits(self) -> None:
        for credit_id, work_id, person_id, role, credited_as in SEED_WORK_CREDITS:
            await self._ensure_published_work_credit(
                credit_id,
                work_id,
                person_id,
                role,
                credited_as=credited_as,
            )

    async def _ensure_published_work_credit(
        self,
        credit_id: UUID,
        work_id: UUID,
        person_id: UUID,
        role: WorkCreditRole,
        *,
        credited_as: str | None,
    ) -> None:
        content = WorkCreditContent.create(
            role=role,
            credited_as=credited_as,
            provenance=SEED_ASSIGNMENT_PROVENANCE,
        )
        async with self._music_uow() as uow:
            existing = await uow.work_credits.get(credit_id)
        if existing is None:
            await self._work_credits.create(work_id, person_id, role, content, credit_id=credit_id)
            await self._work_credits.publish(credit_id)
            return
        if existing.credited_as != content.credited_as or existing.provenance != content.provenance:
            await self._work_credits.replace_content(credit_id, content)
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._work_credits.publish(credit_id)
