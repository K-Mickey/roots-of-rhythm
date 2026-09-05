from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import MusicalWork


class SongListReader(Protocol):
    async def list_published_works(self) -> tuple[MusicalWork, ...]: ...
