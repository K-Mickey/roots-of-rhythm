"""Stub readers for discovery application tests.

These stubs return pre-built read data and perform no filtering or
ordering: the query layer only maps DTOs. Published filtering/batching is
covered by read service unit tests and by infrastructure persistence tests.
"""

from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.public.song_context_reader import SongHistoricalKnowledgeReadData

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import Source
    from roots_of_rhythm.historical_knowledge.public.genre_relation_claim_reader import (
        PublishedGenreRelationClaims,
    )
    from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import RecordingKnowledgeData
    from roots_of_rhythm.music_catalog.domain import Genre, Group, MusicalWork, Recording
    from roots_of_rhythm.music_catalog.public.group_reader import GroupOverviewData
    from roots_of_rhythm.music_catalog.public.performer_reader import PerformerData
    from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import RecordingLyricsProjection
    from roots_of_rhythm.music_catalog.public.recording_reader import (
        RecordingListData,
        RecordingOverviewData,
    )
    from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData
    from roots_of_rhythm.people_catalog.domain import Person
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

    async def get_published(self, _person_id: UUID) -> Person | None:
        return next(iter(self._data.persons), None)

    async def list_published(self) -> tuple[Person, ...]:
        return self._data.persons


class StubSongHistoricalKnowledgeReader:
    def __init__(self, data: SongHistoricalKnowledgeReadData | None = None) -> None:
        self._data = data or SongHistoricalKnowledgeReadData((), ())

    async def get_song_data(
        self,
        _source_version_ids: Collection[UUID],
        _recording_ids: Collection[UUID],
    ) -> SongHistoricalKnowledgeReadData:
        return self._data


class StubGenreReader:
    def __init__(
        self,
        genres: tuple[Genre, ...] = (),
        by_id: dict[UUID, Genre] | None = None,
    ) -> None:
        self._genres = genres
        self._by_id = by_id or {}

    async def list_published(self) -> tuple[Genre, ...]:
        return self._genres

    async def get_published(self, genre_id: UUID) -> Genre | None:
        return self._by_id.get(genre_id)

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]:
        return {genre_id: self._by_id[genre_id] for genre_id in genre_ids if genre_id in self._by_id}


def _empty_group_overview() -> GroupOverviewData:
    from roots_of_rhythm.music_catalog.public.group_reader import GroupOverviewData

    return GroupOverviewData(group=None, assignments=(), genres={}, memberships=())


def _empty_recording_list() -> RecordingListData:
    from roots_of_rhythm.music_catalog.public.recording_reader import RecordingListData

    return RecordingListData(
        recordings=(),
        assignments_by_recording={},
        genres={},
        groups={},
        person_ids=frozenset(),
    )


def _empty_recording_overview() -> RecordingOverviewData:
    from roots_of_rhythm.music_catalog.public.recording_reader import RecordingOverviewData

    return RecordingOverviewData(
        recording=None,
        works={},
        assignments=(),
        genres={},
        groups={},
        person_ids=frozenset(),
    )


def _empty_recording_lyrics() -> RecordingLyricsProjection:
    from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import RecordingLyricsProjection

    return RecordingLyricsProjection(items=())


def _empty_recording_knowledge() -> RecordingKnowledgeData:
    from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import RecordingKnowledgeData

    return RecordingKnowledgeData(listening_guide=None, origin_claims=(), source_access_by_version=())


class StubGroupReader:
    def __init__(
        self,
        groups: tuple[Group, ...] = (),
        by_id: dict[UUID, Group] | None = None,
        overview: GroupOverviewData | None = None,
    ) -> None:
        self._groups = groups
        self._by_id = by_id or {}
        self._overview = overview

    async def list_published(self) -> tuple[Group, ...]:
        return self._groups

    async def get_published_by_ids(self, group_ids: Collection[UUID]) -> dict[UUID, Group]:
        return {group_id: self._by_id[group_id] for group_id in group_ids if group_id in self._by_id}

    async def get_group_overview(self, _group_id: UUID) -> GroupOverviewData:
        return self._overview if self._overview is not None else _empty_group_overview()


class StubPerformerReader:
    def __init__(self, data: PerformerData) -> None:
        self._data = data

    async def get_performer_data(self, _person_id: UUID) -> PerformerData:
        return self._data


class StubSongListReader:
    def __init__(self, works: tuple[MusicalWork, ...] = ()) -> None:
        self._works = works

    async def list_published_works(self) -> tuple[MusicalWork, ...]:
        return self._works


class StubRecordingReader:
    def __init__(
        self,
        list_data: RecordingListData | None = None,
        overview_data: RecordingOverviewData | None = None,
    ) -> None:
        self._list = list_data
        self._overview = overview_data

    async def list_overview(self) -> RecordingListData:
        return self._list if self._list is not None else _empty_recording_list()

    async def get_recording_overview(self, _recording_id: UUID) -> RecordingOverviewData:
        return self._overview if self._overview is not None else _empty_recording_overview()


class StubRecordingLyricsReader:
    def __init__(self, projection: RecordingLyricsProjection | None = None) -> None:
        self._projection = projection

    async def get(self, _recording: Recording) -> RecordingLyricsProjection:
        return self._projection if self._projection is not None else _empty_recording_lyrics()


class StubRecordingKnowledgeReader:
    def __init__(self, data: RecordingKnowledgeData | None = None) -> None:
        self._data = data

    async def get_recording_data(
        self,
        _recording_id: UUID,
        _source_version_ids: Collection[UUID],
    ) -> RecordingKnowledgeData:
        return self._data if self._data is not None else _empty_recording_knowledge()


class StubSourceReader:
    def __init__(self, sources: dict[UUID, Source] | None = None) -> None:
        self._sources = sources or {}

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        return {source_id: self._sources[source_id] for source_id in source_ids if source_id in self._sources}


class StubGenreRelationClaimReader:
    def __init__(self, data: PublishedGenreRelationClaims | None = None) -> None:
        self._data = data

    async def read_for_genre(self, _genre_id: UUID) -> PublishedGenreRelationClaims:
        from roots_of_rhythm.historical_knowledge.public.genre_relation_claim_reader import (
            PublishedGenreRelationClaims,
        )

        return self._data if self._data is not None else PublishedGenreRelationClaims(claims=(), evidence_by_claim={})
