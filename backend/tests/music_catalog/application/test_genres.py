from typing import TYPE_CHECKING, Self
from uuid import UUID

import pytest

from roots_of_rhythm.music_catalog.application import (
    GenreNameConflict,
    GenreNotFound,
    GenreRepository,
    GenreService,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre, GenrePublicationError

if TYPE_CHECKING:
    from types import TracebackType


class FakeGenreRepository:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self._genres = genres

    async def add(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def get(self, genre_id: UUID) -> Genre | None:
        return self._genres.get(genre_id)

    async def get_published(self, genre_id: UUID) -> Genre | None:
        genre = self._genres.get(genre_id)
        return genre if genre is not None and genre.editorial_status is EditorialStatus.PUBLISHED else None

    async def save(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            genre.id != excluding and genre.content.canonical_name.lower() == canonical_name.lower()
            for genre in self._genres.values()
        )


class FakeUnitOfWork:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self.genres: GenreRepository = FakeGenreRepository(genres)
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_service_creates_updates_and_publishes_in_transactions() -> None:
    genres: dict[UUID, Genre] = {}
    units: list[FakeUnitOfWork] = []

    def uow_factory() -> FakeUnitOfWork:
        unit = FakeUnitOfWork(genres)
        units.append(unit)
        return unit

    service = GenreService(uow_factory)
    genre = await service.create(ClassificationContent("Swing"))
    updated = await service.replace_content(genre.id, ClassificationContent("Swing", definition="Jazz genre"))
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
    units: list[FakeUnitOfWork] = []

    def uow_factory() -> FakeUnitOfWork:
        unit = FakeUnitOfWork(genres)
        units.append(unit)
        return unit

    service = GenreService(uow_factory)
    genre = await service.create(ClassificationContent("Swing"))

    with pytest.raises(GenreNameConflict):
        await service.create(ClassificationContent("swing"))
    with pytest.raises(GenrePublicationError):
        await service.publish(genre.id)
    with pytest.raises(GenreNotFound):
        await service.archive(UUID(int=0))

    assert [unit.commits for unit in units] == [1, 0, 0, 0]
    assert all(unit.rollbacks == 1 for unit in units)
