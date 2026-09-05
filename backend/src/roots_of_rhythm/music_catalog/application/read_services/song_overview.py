from asyncio import gather
from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import (
    ClassificationAssignmentRepository,
    GenreRepository,
    GroupRepository,
    LyricsVersionCreditRepository,
    LyricsVersionRelationRepository,
    LyricsVersionRepository,
    MusicalWorkRepository,
    RecordingRepository,
    WorkCreditRepository,
    WorkRelationRepository,
)
from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData

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

type WorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]
type WorkCreditRepositoryFactory = Callable[[Transaction], WorkCreditRepository]
type AssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]
type WorkRelationRepositoryFactory = Callable[[Transaction], WorkRelationRepository]
type LyricsVersionRepositoryFactory = Callable[[Transaction], LyricsVersionRepository]
type LyricsVersionCreditRepositoryFactory = Callable[[Transaction], LyricsVersionCreditRepository]
type LyricsVersionRelationRepositoryFactory = Callable[[Transaction], LyricsVersionRelationRepository]
type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]
type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]


class SongOverviewReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        work_repository_factory: WorkRepositoryFactory,
        work_credit_repository_factory: WorkCreditRepositoryFactory,
        assignment_repository_factory: AssignmentRepositoryFactory,
        work_relation_repository_factory: WorkRelationRepositoryFactory,
        lyrics_repository_factory: LyricsVersionRepositoryFactory,
        lyrics_credit_repository_factory: LyricsVersionCreditRepositoryFactory,
        lyrics_relation_repository_factory: LyricsVersionRelationRepositoryFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
        group_repository_factory: GroupRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._work_repository_factory = work_repository_factory
        self._work_credit_repository_factory = work_credit_repository_factory
        self._assignment_repository_factory = assignment_repository_factory
        self._work_relation_repository_factory = work_relation_repository_factory
        self._lyrics_repository_factory = lyrics_repository_factory
        self._lyrics_credit_repository_factory = lyrics_credit_repository_factory
        self._lyrics_relation_repository_factory = lyrics_relation_repository_factory
        self._recording_repository_factory = recording_repository_factory
        self._genre_repository_factory = genre_repository_factory
        self._group_repository_factory = group_repository_factory

    async def get_song_data(self, song_id: UUID) -> SongMusicReadData:
        async with self._transaction_scope() as transaction:
            work = await self._work_repository_factory(transaction).get_published(song_id)
            if work is None:
                return SongMusicReadData(None)

        (
            work_credits,
            assignments,
            work_relations_and_related,
            lyrics_branch,
            recordings_branch,
        ) = await gather(
            self._load_work_credits(song_id),
            self._load_assignments(song_id),
            self._load_work_relations(song_id),
            self._load_lyrics(song_id),
            self._load_recordings(song_id),
        )
        work_relations, related_works = work_relations_and_related
        lyrics_versions, related_lyrics_versions, lyrics_credits, lyrics_relations = lyrics_branch
        recordings, recording_assignments, groups = recordings_branch

        genre_ids = {item.concept_id for item in assignments}
        recording_genre_ids = {item.concept_id for item in recording_assignments}
        genres_by_id = await self._load_genres(frozenset(genre_ids | recording_genre_ids))

        return SongMusicReadData(
            work=work,
            work_credits=work_credits,
            genres=tuple(genres_by_id[genre_id] for genre_id in sorted(genre_ids) if genre_id in genres_by_id),
            work_relations=work_relations,
            related_works=related_works,
            lyrics_versions=lyrics_versions,
            related_lyrics_versions=related_lyrics_versions,
            lyrics_credits=lyrics_credits,
            lyrics_relations=lyrics_relations,
            recordings=recordings,
            recording_assignments=recording_assignments,
            recording_genres=tuple(
                genres_by_id[genre_id] for genre_id in sorted(recording_genre_ids) if genre_id in genres_by_id
            ),
            groups=groups,
        )

    async def _load_work_credits(self, song_id: UUID) -> tuple[WorkCredit, ...]:
        async with self._transaction_scope() as transaction:
            work_credits = await self._work_credit_repository_factory(transaction).list_published_for_work(song_id)
        return tuple(work_credits)

    async def _load_assignments(self, song_id: UUID) -> tuple[ClassificationAssignment, ...]:
        async with self._transaction_scope() as transaction:
            assignments = await self._assignment_repository_factory(transaction).list_published_for_work(song_id)
        return tuple(assignments)

    async def _load_work_relations(
        self,
        song_id: UUID,
    ) -> tuple[tuple[WorkRelation, ...], tuple[MusicalWork, ...]]:
        async with self._transaction_scope() as transaction:
            work_relations = await self._work_relation_repository_factory(transaction).list_published_for_work(song_id)
            outbound_relations = [item for item in work_relations if item.source_work_id == song_id]
            related_works = await self._work_repository_factory(transaction).get_published_by_ids(
                [item.target_work_id for item in outbound_relations]
            )
        return tuple(work_relations), tuple(related_works.values())

    async def _load_lyrics(
        self,
        song_id: UUID,
    ) -> tuple[
        tuple[LyricsVersion, ...],
        tuple[LyricsVersion, ...],
        tuple[LyricsVersionCredit, ...],
        tuple[LyricsVersionRelation, ...],
    ]:
        async with self._transaction_scope() as transaction:
            lyrics_repository = self._lyrics_repository_factory(transaction)
            lyrics_versions = await lyrics_repository.list_published_for_work(song_id)
            version_ids = [version.id for version in lyrics_versions]
            lyrics_credits = await self._lyrics_credit_repository_factory(transaction).list_published_for_versions(
                version_ids
            )
            lyrics_relations = await self._lyrics_relation_repository_factory(transaction).list_published_for_versions(
                version_ids
            )
            other_lyrics_ids = {
                item.target_lyrics_version_id
                if item.source_lyrics_version_id == version.id
                else item.source_lyrics_version_id
                for version in lyrics_versions
                for item in lyrics_relations.get(version.id, ())
            } - set(version_ids)
            related_lyrics_versions = await lyrics_repository.get_published_by_ids(other_lyrics_ids)
        return (
            tuple(lyrics_versions),
            tuple(related_lyrics_versions.values()),
            tuple(item for items in lyrics_credits.values() for item in items),
            tuple({item.id: item for items in lyrics_relations.values() for item in items}.values()),
        )

    async def _load_recordings(
        self,
        song_id: UUID,
    ) -> tuple[tuple[Recording, ...], tuple[ClassificationAssignment, ...], tuple[Group, ...]]:
        async with self._transaction_scope() as transaction:
            recordings = await self._recording_repository_factory(transaction).list_published_for_work(song_id)
            recording_ids = [recording.id for recording in recordings]
            recording_assignments = await self._assignment_repository_factory(
                transaction
            ).list_published_for_recordings(recording_ids)
            groups = await self._group_repository_factory(transaction).get_published_by_ids(
                {
                    credit.target_id
                    for recording in recordings
                    for credit in recording.credits
                    if credit.is_primary_billing and credit.is_group_target
                },
            )
        return (
            tuple(recordings),
            tuple(item for items in recording_assignments.values() for item in items),
            tuple(groups.values()),
        )

    async def _load_genres(self, genre_ids: frozenset[UUID]) -> dict[UUID, Genre]:
        if not genre_ids:
            return {}
        async with self._transaction_scope() as transaction:
            return await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)
