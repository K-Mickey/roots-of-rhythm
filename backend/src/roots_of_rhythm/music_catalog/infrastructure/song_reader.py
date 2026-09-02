from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork
from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData

if TYPE_CHECKING:
    from uuid import UUID

type MusicUnitOfWorkFactory = Callable[[], RecordingUnitOfWork]


class SqlAlchemySongMusicReader:
    def __init__(self, uow_factory: MusicUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_song_data(self, song_id: UUID) -> SongMusicReadData:
        async with self._uow_factory() as uow:
            work = await uow.works.get_published(song_id)
            if work is None:
                return SongMusicReadData(None)
            work_credits = await uow.work_credits.list_published_for_work(song_id)
            assignments = await uow.assignments.list_published_for_work(song_id)
            work_relations = await uow.work_relations.list_published_for_work(song_id)
            lyrics_versions = await uow.lyrics_versions.list_published_for_work(song_id)
            version_ids = [version.id for version in lyrics_versions]
            lyrics_credits = await uow.lyrics_version_credits.list_published_for_versions(version_ids)
            lyrics_relations = await uow.lyrics_version_relations.list_published_for_versions(version_ids)
            outbound_relations = [item for item in work_relations if item.source_work_id == song_id]
            related_works = await uow.works.get_published_by_ids([item.target_work_id for item in outbound_relations])
            other_lyrics_ids = {
                item.target_lyrics_version_id
                if item.source_lyrics_version_id == version.id
                else item.source_lyrics_version_id
                for version in lyrics_versions
                for item in lyrics_relations.get(version.id, ())
            } - set(version_ids)
            related_lyrics_versions = await uow.lyrics_versions.get_published_by_ids(other_lyrics_ids)
            recordings = await uow.recordings.list_published_for_work(song_id)
            recording_ids = [recording.id for recording in recordings]
            recording_assignments = await uow.assignments.list_published_for_recordings(recording_ids)
            genre_ids = {item.concept_id for item in assignments}
            recording_genre_ids = {item.concept_id for items in recording_assignments.values() for item in items}
            genres_by_id = await uow.genres.get_published_by_ids(
                genre_ids | recording_genre_ids,
            )
            groups = await uow.groups.get_published_by_ids(
                {
                    credit.target_id
                    for recording in recordings
                    for credit in recording.credits
                    if credit.is_primary_billing and credit.is_group_target
                },
            )
        return SongMusicReadData(
            work=work,
            work_credits=tuple(work_credits),
            genres=tuple(genres_by_id[genre_id] for genre_id in sorted(genre_ids) if genre_id in genres_by_id),
            work_relations=tuple(work_relations),
            related_works=tuple(related_works.values()),
            lyrics_versions=tuple(lyrics_versions),
            related_lyrics_versions=tuple(related_lyrics_versions.values()),
            lyrics_credits=tuple(item for items in lyrics_credits.values() for item in items),
            lyrics_relations=tuple(
                {item.id: item for items in lyrics_relations.values() for item in items}.values(),
            ),
            recordings=tuple(recordings),
            recording_assignments=tuple(item for items in recording_assignments.values() for item in items),
            recording_genres=tuple(
                genres_by_id[genre_id] for genre_id in sorted(recording_genre_ids) if genre_id in genres_by_id
            ),
            groups=tuple(groups.values()),
        )
