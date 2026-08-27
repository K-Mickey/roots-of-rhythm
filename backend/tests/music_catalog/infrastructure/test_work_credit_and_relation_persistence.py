from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.application import (
    MusicalWorkService,
    WorkCreditConflict,
    WorkCreditService,
    WorkRelationConflict,
    WorkRelationService,
)
from roots_of_rhythm.music_catalog.domain import (
    WorkContent,
    WorkCreditContent,
    WorkCreditRole,
    WorkRelationContent,
    WorkRelationType,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_work_credit_and_relation_persistence_round_trip(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    credit_service = WorkCreditService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    relation_service = WorkRelationService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))

    source = await work_service.create(WorkContent.create("Derivative Work", provenance="Seed A."))
    target = await work_service.create(WorkContent.create("Original Work", provenance="Seed B."))
    await work_service.publish(source.id)
    await work_service.publish(target.id)

    person_id = uuid7()
    composer = await credit_service.create(source.id, person_id, WorkCreditRole.COMPOSER)
    lyricist = await credit_service.create(
        source.id,
        person_id,
        WorkCreditRole.LYRICIST,
        WorkCreditContent.create(role=WorkCreditRole.LYRICIST, credited_as="Lyric name"),
    )
    await credit_service.publish(composer.id)
    await credit_service.publish(lyricist.id)

    relation = await relation_service.create(
        source.id,
        target.id,
        WorkRelationType.ADAPTATION_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.ADAPTATION_OF,
            provenance="Editorial relation note.",
        ),
    )
    await relation_service.publish(relation.id)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        published_credits = await uow.work_credits.list_published_for_work(source.id)
        relations = await uow.work_relations.list_published_for_work(source.id)

    assert {credit.role for credit in published_credits} == {
        WorkCreditRole.COMPOSER,
        WorkCreditRole.LYRICIST,
    }
    assert published_credits[0].credited_as in {None, "Lyric name"}
    assert len(relations) == 1
    assert relations[0].relation_type is WorkRelationType.ADAPTATION_OF
    assert relations[0].target_work_id == target.id


@pytest.mark.asyncio
async def test_work_credit_duplicate_role_rejected(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    credit_service = WorkCreditService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    work = await work_service.create(WorkContent.create("One O'Clock Jump", provenance="Seed."))
    person_id = uuid7()

    await credit_service.create(work.id, person_id, WorkCreditRole.COMPOSER)
    with pytest.raises(WorkCreditConflict):
        await credit_service.create(work.id, person_id, WorkCreditRole.COMPOSER)


@pytest.mark.asyncio
async def test_work_relation_duplicate_and_soft_delete(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    relation_service = WorkRelationService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))

    source = await work_service.create(WorkContent.create("Derivative", provenance="Seed A."))
    target = await work_service.create(WorkContent.create("Original", provenance="Seed B."))
    await work_service.publish(source.id)
    await work_service.publish(target.id)
    content = WorkRelationContent.create(
        relation_type=WorkRelationType.TRANSLATION_OF,
        provenance="Editorial note.",
    )

    relation = await relation_service.create(source.id, target.id, WorkRelationType.TRANSLATION_OF, content)
    with pytest.raises(WorkRelationConflict):
        await relation_service.create(source.id, target.id, WorkRelationType.TRANSLATION_OF, content)

    await relation_service.publish(relation.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.work_relations.mark_deleted(relation.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.work_relations.get_published(relation.id) is None
