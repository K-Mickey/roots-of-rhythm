from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.music_catalog.application import (
    MusicalWorkService,
    WorkCreditService,
    WorkRelationService,
    WorkRelationWorkNotPublished,
)
from roots_of_rhythm.music_catalog.domain import (
    MusicalWork,
    WorkContent,
    WorkCredit,
    WorkCreditRole,
    WorkRelation,
    WorkRelationContent,
    WorkRelationType,
)

if TYPE_CHECKING:
    from uuid import UUID


@pytest.mark.asyncio
async def test_work_relation_publish_requires_published_endpoints() -> None:
    works: dict[UUID, MusicalWork] = {}
    relations: dict[UUID, WorkRelation] = {}
    work_service = MusicalWorkService(lambda: FakeMusicCatalogUnitOfWork({}, works=works))
    relation_service = WorkRelationService(
        lambda: FakeMusicCatalogUnitOfWork({}, works=works, work_relations=relations)
    )

    source = await work_service.create(WorkContent.create("Derivative", provenance="Seed."))
    target = await work_service.create(WorkContent.create("Original", provenance="Seed."))
    await work_service.publish(target.id)
    relation = await relation_service.create(
        source.id,
        target.id,
        WorkRelationType.ADAPTATION_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.ADAPTATION_OF,
            provenance="Editorial note.",
        ),
    )

    with pytest.raises(WorkRelationWorkNotPublished, match=str(source.id)):
        await relation_service.publish(relation.id)

    await work_service.publish(source.id)
    published = await relation_service.publish(relation.id)

    assert published.is_published


@pytest.mark.asyncio
async def test_work_credit_service_creates_multiple_roles_for_same_person() -> None:
    work_credits: dict[UUID, WorkCredit] = {}
    service = WorkCreditService(lambda: FakeMusicCatalogUnitOfWork({}, work_credits=work_credits))
    work_id = uuid7()
    person_id = uuid7()

    composer = await service.create(work_id, person_id, WorkCreditRole.COMPOSER)
    lyricist = await service.create(work_id, person_id, WorkCreditRole.LYRICIST)
    composer = await service.publish(composer.id)
    lyricist = await service.publish(lyricist.id)

    assert composer.is_published
    assert lyricist.is_published
    assert len(work_credits) == 2
