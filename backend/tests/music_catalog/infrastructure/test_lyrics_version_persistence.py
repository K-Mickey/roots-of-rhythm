from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import Source, SourceAccessPolicy, SourceVersion
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.application import (
    RIGHTS_RESTRICTED_REASON,
    LyricsVersionConflict,
    LyricsVersionProjectionService,
    LyricsVersionRelationService,
    LyricsVersionService,
    MusicalWorkService,
)
from roots_of_rhythm.music_catalog.domain import (
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionContent,
    LyricsVersionRelationContent,
    LyricsVersionRelationType,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from tests.support.postgres import collect_select_statements

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_lyrics_version_persistence_round_trip_and_order(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    lyrics_service = LyricsVersionService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    relation_service = LyricsVersionRelationService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))

    def hk_uow_factory() -> SqlAlchemyHistoricalKnowledgeUnitOfWork:
        return SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory)

    projection = LyricsVersionProjectionService(
        lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory),
        hk_uow_factory,
    )

    async with hk_uow_factory() as hk:
        source = Source.create("Lyrics corpus", access_policy=SourceAccessPolicy.ALLOW_PUBLIC_BODY)
        source_version = SourceVersion.create(source.id, "edition-1")
        await hk.sources.add_source(source)
        await hk.sources.add_version(source_version)
        await hk.commit()

    from roots_of_rhythm.music_catalog.domain import WorkContent

    work = await work_service.create(WorkContent.create("One O'Clock Jump", provenance="Seed."))
    second_work = await work_service.create(WorkContent.create("Jumpin' at the Woodside", provenance="Seed."))
    performable = await lyrics_service.create(
        work.id,
        source_version.id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
            body="Jumpin' at the woodside",
        ),
    )
    reading = await lyrics_service.create(
        work.id,
        source_version.id,
        LyricsVersionContent.create(
            language_tag="ru",
            usage_kind=LyricsUsageKind.READING_TRANSLATION,
            creation_method=LyricsCreationMethod.HUMAN_TRANSLATION,
            label="Reading",
            body="Перевод для чтения",
        ),
    )
    await lyrics_service.publish(performable.id)
    await lyrics_service.publish(reading.id)
    await work_service.publish(second_work.id)
    second_performable = await lyrics_service.create(
        second_work.id,
        source_version.id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
        ),
    )
    second_performable = await lyrics_service.publish(second_performable.id)

    relation = await relation_service.create(
        reading.id,
        performable.id,
        LyricsVersionRelationType.TRANSLATION_OF,
        LyricsVersionRelationContent.create(
            relation_type=LyricsVersionRelationType.TRANSLATION_OF,
            provenance="Editorial relation note.",
        ),
    )
    await relation_service.publish(relation.id)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        published_versions = await uow.lyrics_versions.list_published_for_work(work.id)
        published_versions_by_work = await uow.lyrics_versions.list_published_for_works([second_work.id, work.id])
        relations = await uow.lyrics_version_relations.list_published_for_version(reading.id)

    assert [version.usage_kind for version in published_versions] == [
        LyricsUsageKind.PERFORMABLE,
        LyricsUsageKind.READING_TRANSLATION,
    ]
    assert published_versions[0].language_tag == "en"
    assert published_versions[1].language_tag == "ru"
    assert published_versions_by_work == {
        work.id: published_versions,
        second_work.id: [second_performable],
    }
    assert len(relations) == 1
    assert relations[0].is_translation_of

    disclosure = await projection.disclose_body_for_version(published_versions[0])
    assert disclosure.body == "Jumpin' at the woodside"
    assert disclosure.body_unavailable_reason is None


@pytest.mark.asyncio
async def test_lyrics_version_batch_read_skips_empty_input(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        with collect_select_statements() as selects:
            versions = await uow.lyrics_versions.list_published_for_works([])

    assert versions == {}
    assert selects == []


@pytest.mark.asyncio
async def test_lyrics_version_duplicate_rejected(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    lyrics_service = LyricsVersionService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    source_version_id = uuid7()
    from roots_of_rhythm.music_catalog.domain import WorkContent

    work = await work_service.create(WorkContent.create("Ornithology", provenance="Seed."))
    content = LyricsVersionContent.create(
        language_tag="en",
        usage_kind=LyricsUsageKind.PERFORMABLE,
        creation_method=LyricsCreationMethod.ORIGINAL,
    )
    await lyrics_service.create(work.id, source_version_id, content)
    with pytest.raises(LyricsVersionConflict):
        await lyrics_service.create(work.id, source_version_id, content)


@pytest.mark.asyncio
async def test_lyrics_body_withheld_when_source_policy_withholds(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    lyrics_service = LyricsVersionService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))

    def hk_uow_factory() -> SqlAlchemyHistoricalKnowledgeUnitOfWork:
        return SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory)

    projection = LyricsVersionProjectionService(
        lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory),
        hk_uow_factory,
    )

    async with hk_uow_factory() as hk:
        source = Source.create("Restricted lyrics")
        source_version = SourceVersion.create(source.id, "edition-1")
        await hk.sources.add_source(source)
        await hk.sources.add_version(source_version)
        await hk.commit()

    from roots_of_rhythm.music_catalog.domain import WorkContent

    work = await work_service.create(WorkContent.create("West End Blues", provenance="Seed."))
    version = await lyrics_service.create(
        work.id,
        source_version.id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
            body="Hidden lyrics",
        ),
    )
    published = await lyrics_service.publish(version.id)
    disclosure = await projection.disclose_body_for_version(published)

    assert disclosure.body is None
    assert disclosure.body_unavailable_reason == RIGHTS_RESTRICTED_REASON


@pytest.mark.asyncio
async def test_lyrics_version_soft_delete(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    lyrics_service = LyricsVersionService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    from roots_of_rhythm.music_catalog.application import MusicalWorkService
    from roots_of_rhythm.music_catalog.domain import WorkContent

    work_service = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    work = await work_service.create(WorkContent.create("Sixteen Tons", provenance="Seed."))
    version = await lyrics_service.create(
        work.id,
        uuid7(),
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
        ),
    )
    await lyrics_service.publish(version.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.lyrics_versions.mark_deleted(version.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.lyrics_versions.get_published(version.id) is None
