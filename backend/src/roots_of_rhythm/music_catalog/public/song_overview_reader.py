from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
        MusicalWork,
        Recording,
        WorkCredit,
        WorkRelation,
    )


@dataclass(frozen=True, slots=True)
class SongMusicReadData:
    work: MusicalWork | None
    work_credits: tuple[WorkCredit, ...] = ()
    genres: tuple[Genre, ...] = ()
    work_relations: tuple[WorkRelation, ...] = ()
    related_works: tuple[MusicalWork, ...] = ()
    lyrics_versions: tuple[LyricsVersion, ...] = ()
    related_lyrics_versions: tuple[LyricsVersion, ...] = ()
    lyrics_credits: tuple[LyricsVersionCredit, ...] = ()
    lyrics_relations: tuple[LyricsVersionRelation, ...] = ()
    recordings: tuple[Recording, ...] = ()
    recording_assignments: tuple[ClassificationAssignment, ...] = ()
    recording_genres: tuple[Genre, ...] = ()
    groups: tuple[Group, ...] = ()


class SongMusicReader(Protocol):
    async def get_song_data(self, song_id: UUID) -> SongMusicReadData: ...
