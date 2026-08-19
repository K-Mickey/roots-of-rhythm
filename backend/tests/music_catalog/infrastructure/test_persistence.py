from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import inspect

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.application import (
    ClassificationAssignmentService,
    GenreNameConflict,
    GenreService,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.domain import (
    ClassificationContent,
    EditorialStatus,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_migration_created_classification_concepts(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        table_names = await connection.run_sync(lambda sync_connection: inspect(sync_connection).get_table_names())

    assert "classification_concepts" in table_names


@pytest.mark.asyncio
async def test_repository_round_trip_and_public_filter(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    service = GenreService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    image_id = uuid7()
    content = ClassificationContent.create(
        "Swing",
        aliases=("Big-band swing",),
        definition="A jazz genre.",
        boundaries="Not every jazz recording with syncopation is Swing.",
        period=HistoricalPeriod.create(
            "late 1920s–1940s",
            TemporalBound(1920, TemporalPrecision.LATE_DECADE),
            TemporalBound(1940, TemporalPrecision.DECADE),
        ),
        geography=GeographicContext.create("United States"),
        historical_context="Developed during the big-band era.",
        formation="Formed from earlier jazz practices.",
        characteristic_features=("Four-beat rhythm", "Riff-based arrangements"),
        primary_image_id=image_id,
    )

    draft = await service.create(content)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.genres.get_published(draft.id) is None

    published = await service.publish(draft.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.genres.get_published(draft.id)

    assert loaded == published
    assert loaded is not None and loaded.content.primary_image_id == image_id

    jump = await service.create(ClassificationContent.create("Jump Blues", definition="A related genre."))
    await service.publish(jump.id)
    draft_only = await service.create(ClassificationContent.create("Unpublished", definition="Still draft."))
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        listed = await uow.genres.list_published()
    assert [genre.content.canonical_name for genre in listed] == ["Jump Blues", "Swing"]
    assert draft_only.id not in {genre.id for genre in listed}

    await service.archive(draft.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.genres.get_published(draft.id) is None


@pytest.mark.asyncio
async def test_assignment_repository_round_trips_publication_content(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    genres = GenreService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    assignments = ClassificationAssignmentService(
        lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory),
        lambda _: _published(True),
    )
    jazz = await genres.create(ClassificationContent.create("Jazz", definition="A genre."))
    await genres.publish(jazz.id)
    person_id = uuid7()
    claim_id = uuid7()
    assignment = await assignments.create_for_person(
        person_id,
        jazz.id,
        claim_id=claim_id,
        provenance="Editorial review.",
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    published = await assignments.publish(assignment.id)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.assignments.get(assignment.id)
        listed = await uow.assignments.list_published_for_person(person_id)

    assert loaded == published
    assert loaded is not None
    assert loaded.claim_id == claim_id
    assert loaded.explanation is None
    assert loaded.provenance == "Editorial review."
    assert loaded.evidence_status is EvidenceStatus.UNVERIFIED
    assert listed == [published]


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_and_unique_name_is_case_insensitive(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    service = GenreService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    genre = await service.create(ClassificationContent.create("Swing"))

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.genres.save(genre.submit_for_review())

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.genres.get(genre.id)
    assert loaded is not None and loaded.editorial_status is EditorialStatus.DRAFT

    with pytest.raises(GenreNameConflict):
        await service.create(ClassificationContent.create("SWING"))

    duplicate = await service.create(ClassificationContent.create("Jump Blues"))
    duplicate_case = duplicate.replace_content(ClassificationContent.create("swing"))
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.genres.save(duplicate_case)
        with pytest.raises(UniqueConstraintViolation):
            await uow.commit()

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.genres.mark_deleted(genre.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.genres.get(genre.id) is None
    recreated = await service.create(ClassificationContent.create("Swing"))
    assert recreated.id != genre.id


async def _published(value: bool) -> bool:
    return value
