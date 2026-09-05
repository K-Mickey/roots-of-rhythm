from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import LyricsVersion, Recording


@dataclass(frozen=True, slots=True)
class RecordingLyricsSelection:
    version: LyricsVersion
    position: int | None
    confirmed_for_recording: bool
    reading_translations: tuple[LyricsVersion, ...] = ()


@dataclass(frozen=True, slots=True)
class RecordingLyricsProjection:
    items: tuple[RecordingLyricsSelection, ...] = ()


class RecordingLyricsReader(Protocol):
    async def get(self, recording: Recording) -> RecordingLyricsProjection: ...
