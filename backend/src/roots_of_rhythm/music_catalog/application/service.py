from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    GenreNameConflict,
    GenreNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import ClassificationContent, Genre

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class GenreService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(self, content: ClassificationContent) -> Genre:
        async with self._uow_factory() as uow:
            await self._ensure_name_available(uow, content.canonical_name)
            genre = Genre(id=uuid7(), content=content)
            await uow.genres.add(genre)
            await self._commit(uow)
            return genre

    async def replace_content(self, genre_id: UUID, content: ClassificationContent) -> Genre:
        async with self._uow_factory() as uow:
            genre = await self._get(uow, genre_id)
            await self._ensure_name_available(uow, content.canonical_name, excluding=genre_id)
            updated = genre.replace_content(content)
            try:
                await uow.genres.save(updated)
            except LookupError as error:
                raise GenreNotFound(str(genre_id)) from error
            await self._commit(uow)
            return updated

    async def submit_for_review(self, genre_id: UUID) -> Genre:
        return await self._change_status(genre_id, Genre.submit_for_review)

    async def publish(self, genre_id: UUID) -> Genre:
        return await self._change_status(genre_id, Genre.publish)

    async def archive(self, genre_id: UUID) -> Genre:
        return await self._change_status(genre_id, Genre.archive)

    async def _change_status(self, genre_id: UUID, transition: Callable[[Genre], Genre]) -> Genre:
        async with self._uow_factory() as uow:
            genre = await self._get(uow, genre_id)
            updated = transition(genre)
            try:
                await uow.genres.save(updated)
            except LookupError as error:
                raise GenreNotFound(str(genre_id)) from error
            await self._commit(uow)
            return updated

    @staticmethod
    async def _commit(uow: MusicCatalogUnitOfWork) -> None:
        try:
            await uow.commit()
        except UniqueConstraintViolation as error:
            raise GenreNameConflict from error

    @staticmethod
    async def _get(uow: MusicCatalogUnitOfWork, genre_id: UUID) -> Genre:
        genre = await uow.genres.get(genre_id)
        if genre is None:
            raise GenreNotFound(str(genre_id))
        return genre

    @staticmethod
    async def _ensure_name_available(
        uow: MusicCatalogUnitOfWork,
        canonical_name: str,
        *,
        excluding: UUID | None = None,
    ) -> None:
        if await uow.genres.canonical_name_exists(canonical_name, excluding=excluding):
            raise GenreNameConflict(canonical_name)
