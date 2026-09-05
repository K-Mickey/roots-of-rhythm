from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

from litestar.di import Provide

from roots_of_rhythm.discovery.application.queries.genre_list import GenreListQuery
from roots_of_rhythm.discovery.application.queries.genre_overview import GenreOverviewQuery
from roots_of_rhythm.discovery.application.queries.genre_relations import GenreRelationsQuery
from roots_of_rhythm.discovery.application.queries.genre_sources import GenreSourcesQuery
from roots_of_rhythm.discovery.application.queries.group_list import GroupListQuery
from roots_of_rhythm.discovery.application.queries.group_overview import GroupOverviewQuery
from roots_of_rhythm.discovery.application.queries.performer_list import PerformerListQuery
from roots_of_rhythm.discovery.application.queries.performer_overview import PerformerOverviewQuery
from roots_of_rhythm.discovery.application.queries.recording_list import RecordingListQuery
from roots_of_rhythm.discovery.application.queries.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.discovery.application.queries.song_list import SongListQuery
from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewQuery
from roots_of_rhythm.historical_knowledge.application import (
    GenreRelationClaimReadService,
    RecordingKnowledgeReadService,
    SongContextReadService,
    SourceReadService,
)
from roots_of_rhythm.historical_knowledge.infrastructure.claim_repository import SqlAlchemyClaimRepository
from roots_of_rhythm.historical_knowledge.infrastructure.listening_guide_repository import (
    SqlAlchemyListeningGuideRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.recording_origin_claim_repository import (
    SqlAlchemyRecordingOriginClaimRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.application import (
    GenreReadService,
    GroupReadService,
    PerformerReadService,
    RecordingLyricsReadService,
    RecordingReadService,
    SongListReadService,
    SongOverviewReadService,
)
from roots_of_rhythm.music_catalog.infrastructure.assignment_repository import (
    SqlAlchemyClassificationAssignmentRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.group_membership_repository import (
    SqlAlchemyGroupMembershipRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.group_repository import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_credit_repository import (
    SqlAlchemyLyricsVersionCreditRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_relation_repository import (
    SqlAlchemyLyricsVersionRelationRepository,
)
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_repository import SqlAlchemyLyricsVersionRepository
from roots_of_rhythm.music_catalog.infrastructure.musical_work_repository import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.work_credit_repository import SqlAlchemyWorkCreditRepository
from roots_of_rhythm.music_catalog.infrastructure.work_relation_repository import SqlAlchemyWorkRelationRepository
from roots_of_rhythm.people_catalog.application import PersonsReadService
from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.transaction import Transaction


GENRE_LIST_READER_DEPENDENCY = "genre_list_reader"
GENRE_OVERVIEW_READER_DEPENDENCY = "genre_overview_reader"
GENRE_RELATIONS_READER_DEPENDENCY = "genre_relations_reader"
GENRE_SOURCES_READER_DEPENDENCY = "genre_sources_reader"
PERFORMER_LIST_READER_DEPENDENCY = "performer_list_reader"
PERFORMER_OVERVIEW_READER_DEPENDENCY = "performer_overview_reader"
GROUP_LIST_READER_DEPENDENCY = "group_list_reader"
GROUP_OVERVIEW_READER_DEPENDENCY = "group_overview_reader"
SONG_LIST_READER_DEPENDENCY = "song_list_reader"
SONG_OVERVIEW_READER_DEPENDENCY = "song_overview_reader"
RECORDING_LIST_READER_DEPENDENCY = "recording_list_reader"
RECORDING_OVERVIEW_READER_DEPENDENCY = "recording_overview_reader"

type DependencyProviders = Mapping[str, Provide]


def repository_factory[T](repository_type: Callable[[AsyncSession], T]) -> Callable[[Transaction], T]:
    def factory(transaction: Transaction) -> T:
        return repository_type(sqlalchemy_session(transaction))

    return factory


def create_api_dependencies(
    session_factory: async_sessionmaker[AsyncSession],
    overrides: DependencyProviders | None = None,
) -> dict[str, Provide]:
    transaction_scope = SqlAlchemyTransactionScope(session_factory)

    genre_repo = repository_factory(SqlAlchemyGenreRepository)
    group_repo = repository_factory(SqlAlchemyGroupRepository)
    assignment_repo = repository_factory(SqlAlchemyClassificationAssignmentRepository)
    membership_repo = repository_factory(SqlAlchemyGroupMembershipRepository)
    work_repo = repository_factory(SqlAlchemyMusicalWorkRepository)
    work_credit_repo = repository_factory(SqlAlchemyWorkCreditRepository)
    work_relation_repo = repository_factory(SqlAlchemyWorkRelationRepository)
    lyrics_repo = repository_factory(SqlAlchemyLyricsVersionRepository)
    lyrics_credit_repo = repository_factory(SqlAlchemyLyricsVersionCreditRepository)
    lyrics_relation_repo = repository_factory(SqlAlchemyLyricsVersionRelationRepository)
    recording_repo = repository_factory(SqlAlchemyRecordingRepository)
    person_repo = repository_factory(SqlAlchemyPersonRepository)
    claim_repo = repository_factory(SqlAlchemyClaimRepository)
    listening_guide_repo = repository_factory(SqlAlchemyListeningGuideRepository)
    origin_claim_repo = repository_factory(SqlAlchemyRecordingOriginClaimRepository)
    source_repo = repository_factory(SqlAlchemySourceRepository)

    genres = GenreReadService(transaction_scope, genre_repo)
    groups = GroupReadService(transaction_scope, group_repo, assignment_repo, membership_repo, genre_repo)
    performers = PerformerReadService(transaction_scope, assignment_repo, genre_repo)
    songs = SongListReadService(transaction_scope, work_repo)
    song_overview = SongOverviewReadService(
        transaction_scope,
        work_repo,
        work_credit_repo,
        assignment_repo,
        work_relation_repo,
        lyrics_repo,
        lyrics_credit_repo,
        lyrics_relation_repo,
        recording_repo,
        genre_repo,
        group_repo,
    )
    recordings = RecordingReadService(
        transaction_scope,
        recording_repo,
        assignment_repo,
        work_repo,
        genre_repo,
        group_repo,
    )
    recording_lyrics = RecordingLyricsReadService(transaction_scope, lyrics_repo, lyrics_relation_repo)
    people = PersonsReadService(transaction_scope, person_repo)
    song_context = SongContextReadService(transaction_scope, origin_claim_repo, source_repo)
    genre_relation_claims = GenreRelationClaimReadService(transaction_scope, claim_repo, source_repo)
    sources = SourceReadService(transaction_scope, source_repo)
    recording_knowledge = RecordingKnowledgeReadService(
        transaction_scope,
        listening_guide_repo,
        origin_claim_repo,
        source_repo,
    )

    list_query = GenreListQuery(genres)
    overview_query = GenreOverviewQuery(genres)
    performer_list_query = PerformerListQuery(people)
    performer_overview_query = PerformerOverviewQuery(people, performers)
    group_list_query = GroupListQuery(groups)
    group_overview_query = GroupOverviewQuery(groups, people)
    song_list_query = SongListQuery(songs)
    song_overview_query = SongOverviewQuery(song_overview, people, song_context)
    recording_list_query = RecordingListQuery(recordings, people)
    recording_overview_query = RecordingOverviewQuery(recordings, people, recording_lyrics, recording_knowledge)
    relations_query = GenreRelationsQuery(genres, genre_relation_claims)
    sources_query = GenreSourcesQuery(genres, genre_relation_claims, sources)

    dependencies = {
        GENRE_LIST_READER_DEPENDENCY: Provide(lambda: list_query, sync_to_thread=False),
        GENRE_OVERVIEW_READER_DEPENDENCY: Provide(lambda: overview_query, sync_to_thread=False),
        GENRE_RELATIONS_READER_DEPENDENCY: Provide(lambda: relations_query, sync_to_thread=False),
        GENRE_SOURCES_READER_DEPENDENCY: Provide(lambda: sources_query, sync_to_thread=False),
        PERFORMER_LIST_READER_DEPENDENCY: Provide(lambda: performer_list_query, sync_to_thread=False),
        PERFORMER_OVERVIEW_READER_DEPENDENCY: Provide(lambda: performer_overview_query, sync_to_thread=False),
        GROUP_LIST_READER_DEPENDENCY: Provide(lambda: group_list_query, sync_to_thread=False),
        GROUP_OVERVIEW_READER_DEPENDENCY: Provide(lambda: group_overview_query, sync_to_thread=False),
        SONG_LIST_READER_DEPENDENCY: Provide(lambda: song_list_query, sync_to_thread=False),
        SONG_OVERVIEW_READER_DEPENDENCY: Provide(lambda: song_overview_query, sync_to_thread=False),
        RECORDING_LIST_READER_DEPENDENCY: Provide(lambda: recording_list_query, sync_to_thread=False),
        RECORDING_OVERVIEW_READER_DEPENDENCY: Provide(lambda: recording_overview_query, sync_to_thread=False),
    }
    if overrides is not None:
        dependencies.update(overrides)
    return dependencies
