from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.domain import EditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.seed import musical_works as data
from roots_of_rhythm.seed import people_and_groups as artist_data
from tests.support.seed import run_corpus_seed

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from roots_of_rhythm.application.ports import DbAccessor, UnitOfWork

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_musical_works_seed(engine: AsyncEngine, database: DbAccessor, uow: UnitOfWork) -> None:
    session_factory = create_session_factory(engine)
    await run_corpus_seed(engine, database, uow)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as musical_uow:
        works = await musical_uow.works.list_published()
        work_credits = [await musical_uow.work_credits.get(credit_id) for credit_id, *_ in data.SEED_WORK_CREDITS]

    assert [work.canonical_title for work in works] == sorted(
        content.canonical_title for _, content in data.SEED_MUSICAL_WORKS
    )
    assert all(work.is_published for work in works)
    assert [
        None if credit is None else (credit.editorial_status, credit.role, credit.credited_as, credit.provenance)
        for credit in work_credits
    ] == [
        (EditorialStatus.PUBLISHED, role, credited_as, artist_data.SEED_ASSIGNMENT_PROVENANCE)
        for _, _, _, role, credited_as in data.SEED_WORK_CREDITS
    ]
