from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.application import MusicalWorkService
from roots_of_rhythm.music_catalog.domain import (
    ExistencePeriod,
    ExternalIdentity,
    MusicalWorkPublicationError,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_musical_work_repository_round_trip_and_filter_published(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    period = ExistencePeriod.create(
        start=TemporalBound(1937, TemporalPrecision.EXACT_YEAR),
        end=TemporalBound(1945, TemporalPrecision.CIRCA_YEAR),
    )
    content = WorkContent.create(
        "One O'Clock Jump",
        aliases=("Jump",),
        description="A swing standard.",
        period=period,
        external_identities=(ExternalIdentity.create("MusicBrainz", "work-123", url="https://example.com/work"),),
        provenance="Editorial seed note.",
    )
    published = await work_service.create(content)
    duplicate = await work_service.create(
        WorkContent.create("One O'Clock Jump", provenance="Second seed note."),
    )
    await work_service.publish(published.id)
    await work_service.publish(duplicate.id)
    archived = await work_service.create(
        WorkContent.create("Archived Work", provenance="Archived seed."),
    )
    await work_service.publish(archived.id)
    await work_service.archive(archived.id)
    draft = await work_service.create(WorkContent.create("Draft Work", provenance="Draft seed."))

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.works.get_published(published.id)
        listed = await uow.works.list_published()

    assert loaded is not None
    assert loaded.canonical_title == content.canonical_title
    assert loaded.aliases == content.aliases
    assert loaded.description == content.description
    assert loaded.period == content.period
    assert loaded.external_identities == content.external_identities
    assert loaded.provenance == content.provenance
    assert {work.id for work in listed} == {published.id, duplicate.id}
    assert draft.id not in {work.id for work in listed}
    assert archived.id not in {work.id for work in listed}

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.works.mark_deleted(published.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.works.get(published.id) is None
        assert await uow.works.get_published(published.id) is None


@pytest.mark.asyncio
async def test_musical_work_publish_without_provenance_fails_before_persistence(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    work = await work_service.create(WorkContent.create("Ornithology"))

    with pytest.raises(MusicalWorkPublicationError, match="provenance"):
        await work_service.publish(work.id)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.works.get(work.id)

    assert loaded is not None
    assert loaded.provenance is None
