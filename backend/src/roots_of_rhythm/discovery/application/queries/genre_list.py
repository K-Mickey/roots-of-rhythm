from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import GenreSummary
from roots_of_rhythm.discovery.application.dto.genres import GenreListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.public.genre_reader import GenreReader


@runtime_checkable
class GenreListReader(Protocol):
    async def list(self) -> GenreListResponse: ...


class GenreListQuery:
    def __init__(self, genres: GenreReader) -> None:
        self._genres = genres

    async def list(self) -> GenreListResponse:
        genres = await self._genres.list_published()
        return GenreListResponse(
            items=[GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres],
        )
