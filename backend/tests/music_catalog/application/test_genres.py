from uuid import UUID

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.music_catalog.application import (
    GenreNameConflict,
    GenreNotFound,
    GenreService,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre, GenrePublicationError


@pytest.mark.asyncio
async def test_service_creates_updates_and_publishes_in_transactions() -> None:
    genres: dict[UUID, Genre] = {}
    units: list[FakeMusicCatalogUnitOfWork] = []

    def uow_factory() -> FakeMusicCatalogUnitOfWork:
        unit = FakeMusicCatalogUnitOfWork(genres)
        units.append(unit)
        return unit

    service = GenreService(uow_factory)
    genre = await service.create(ClassificationContent.create("Swing"))
    updated = await service.replace_content(
        genre.id,
        ClassificationContent.create("Swing", definition="Jazz genre"),
    )
    reviewed = await service.submit_for_review(genre.id)
    published = await service.publish(genre.id)
    archived = await service.archive(genre.id)

    assert genre.id == updated.id == reviewed.id == published.id == archived.id
    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert archived.editorial_status is EditorialStatus.ARCHIVED
    assert all(unit.commits == 1 and unit.rollbacks == 1 for unit in units)


@pytest.mark.asyncio
async def test_service_reports_domain_and_application_failures_without_commit() -> None:
    genres: dict[UUID, Genre] = {}
    units: list[FakeMusicCatalogUnitOfWork] = []

    def uow_factory() -> FakeMusicCatalogUnitOfWork:
        unit = FakeMusicCatalogUnitOfWork(genres)
        units.append(unit)
        return unit

    service = GenreService(uow_factory)
    genre = await service.create(ClassificationContent.create("Swing"))

    with pytest.raises(GenreNameConflict):
        await service.create(ClassificationContent.create("swing"))
    with pytest.raises(GenrePublicationError):
        await service.publish(genre.id)
    with pytest.raises(GenreNotFound):
        await service.archive(UUID(int=0))

    assert [unit.commits for unit in units] == [1, 0, 0, 0]
    assert all(unit.rollbacks == 1 for unit in units)
