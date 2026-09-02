from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, EditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import people_and_groups as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_people_and_groups_seed_and_assignment_repair(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    runner = CorpusSeedRunner(session_factory)
    await runner.run()

    async with SqlAlchemyPeopleCatalogUnitOfWork(session_factory) as uow:
        persons = [
            await uow.persons.get_published(person_id)
            for person_id, _ in (*data.SEED_PERFORMERS, *data.SEED_SONG_AUTHORS, *data.SEED_RECORDING_PERFORMERS)
        ]
    assert [person.canonical_name for person in persons if person is not None] == [
        name for _, name in (*data.SEED_PERFORMERS, *data.SEED_SONG_AUTHORS, *data.SEED_RECORDING_PERFORMERS)
    ]
    assert all(person is not None and person.editorial_status is PersonEditorialStatus.PUBLISHED for person in persons)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        groups = [await uow.groups.get_published(group_id) for group_id, _ in data.SEED_GROUPS]
        assignments = [
            await uow.assignments.get(assignment_id)
            for assignment_id, *_ in (*data.SEED_PERSON_GENRE_ASSIGNMENTS, *data.SEED_GROUP_GENRE_ASSIGNMENTS)
        ]
    assert [group.canonical_name for group in groups if group is not None] == [
        content.canonical_name for _, content in data.SEED_GROUPS
    ]
    assert all(assignment is not None and assignment.is_published for assignment in assignments)

    assignment_id, _, _, explanation, provenance = data.SEED_PERSON_GENRE_ASSIGNMENTS[0]
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assignment = await uow.assignments.get(assignment_id)
        assert assignment is not None
        await uow.assignments.save(
            ClassificationAssignment(
                id=assignment.id,
                target_kind=assignment.target_kind,
                target_id=assignment.target_id,
                concept_id=assignment.concept_id,
                editorial_status=assignment.editorial_status,
            )
        )
        await uow.commit()

    await runner.run()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        repaired = await uow.assignments.get(assignment_id)
    assert repaired is not None
    assert (repaired.explanation, repaired.provenance, repaired.editorial_status) == (
        explanation,
        provenance,
        EditorialStatus.PUBLISHED,
    )
