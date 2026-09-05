from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import SongSummary
from roots_of_rhythm.discovery.application.dto.songs import SongListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.public.song_list_reader import SongListReader as MusicSongListReader


@runtime_checkable
class SongListReader(Protocol):
    async def list(self) -> SongListResponse: ...


class SongListQuery:
    def __init__(self, songs: MusicSongListReader) -> None:
        self._songs = songs

    async def list(self) -> SongListResponse:
        works = await self._songs.list_published_works()
        return SongListResponse(
            items=[SongSummary(id=str(work.id), name=work.canonical_title) for work in works],
        )
