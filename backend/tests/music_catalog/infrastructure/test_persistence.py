from os import environ
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import delete, inspect

from roots_of_rhythm.infrastructure.database import create_database_engine, create_session_factory
from roots_of_rhythm.music_catalog.application import GenreNameConflict, GenreService, UniqueConstraintViolation
from roots_of_rhythm.music_catalog.domain import (
    ClassificationContent,
    EditorialStatus,
    GeographicContext,
    HistoricalPeriod,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_url = environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://roots:roots@127.0.0.1:5432/roots_of_rhythm",
    )
    database_engine = create_database_engine(database_url)
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClassificationConceptRecord))
    yield database_engine
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClassificationConceptRecord))
    await database_engine.dispose()


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

    await service.archive(draft.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.genres.get_published(draft.id) is None


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
