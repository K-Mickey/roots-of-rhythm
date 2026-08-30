from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.public.song_context_reader import SongHistoricalKnowledgeReadData

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData


class StubSongMusicReader:
    def __init__(self, data: SongMusicReadData) -> None:
        self._data = data

    async def get_song_data(self, _song_id: UUID) -> SongMusicReadData:
        return self._data


class StubPublishedPeopleReader:
    def __init__(self, data: PublishedPeopleReadData) -> None:
        self._data = data

    async def get_published_by_ids(self, _person_ids: Collection[UUID]) -> PublishedPeopleReadData:
        return self._data


class StubSongHistoricalKnowledgeReader:
    def __init__(self, data: SongHistoricalKnowledgeReadData | None = None) -> None:
        self._data = data or SongHistoricalKnowledgeReadData((), ())

    async def get_song_data(
        self,
        _source_version_ids: Collection[UUID],
        _recording_ids: Collection[UUID],
    ) -> SongHistoricalKnowledgeReadData:
        return self._data
