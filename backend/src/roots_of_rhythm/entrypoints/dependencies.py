from collections.abc import Mapping
from typing import TYPE_CHECKING

from litestar.di import Provide

from roots_of_rhythm.discovery.application.genre_list import GenreListQuery
from roots_of_rhythm.discovery.application.genre_overview import GenreOverviewQuery
from roots_of_rhythm.discovery.application.genre_relations import GenreRelationsQuery
from roots_of_rhythm.discovery.application.genre_sources import GenreSourcesQuery
from roots_of_rhythm.discovery.application.group_list import GroupListQuery
from roots_of_rhythm.discovery.application.group_overview import GroupOverviewQuery
from roots_of_rhythm.discovery.application.performer_list import PerformerListQuery
from roots_of_rhythm.discovery.application.performer_overview import PerformerOverviewQuery
from roots_of_rhythm.discovery.application.recording_list import RecordingListQuery
from roots_of_rhythm.discovery.application.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.discovery.application.song_list import SongListQuery
from roots_of_rhythm.discovery.application.song_overview import SongOverviewQuery
from roots_of_rhythm.historical_knowledge.application import ClaimService, RecordingOriginClaimService, SourceService
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.write_scopes import knowledge_music_scope
from roots_of_rhythm.music_catalog.application import GroupMembershipService, GroupService
from roots_of_rhythm.music_catalog.application.lyrics_version_projection_service import LyricsVersionProjectionService
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
GROUP_SERVICE_DEPENDENCY = "group_service"
GROUP_MEMBERSHIP_SERVICE_DEPENDENCY = "group_membership_service"
RECORDING_ORIGIN_CLAIM_SERVICE_DEPENDENCY = "recording_origin_claim_service"

type DependencyProviders = Mapping[str, Provide]


def create_api_dependencies(
    session_factory: async_sessionmaker[AsyncSession],
    overrides: DependencyProviders | None = None,
) -> dict[str, Provide]:
    def music_uow_factory() -> SqlAlchemyMusicCatalogUnitOfWork:
        return SqlAlchemyMusicCatalogUnitOfWork(session_factory)

    def people_uow_factory() -> SqlAlchemyPeopleCatalogUnitOfWork:
        return SqlAlchemyPeopleCatalogUnitOfWork(session_factory)

    def hk_uow_factory() -> SqlAlchemyHistoricalKnowledgeUnitOfWork:
        return SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory)

    list_query = GenreListQuery(music_uow_factory)
    overview_query = GenreOverviewQuery(music_uow_factory)
    performer_list_query = PerformerListQuery(people_uow_factory)
    performer_overview_query = PerformerOverviewQuery(people_uow_factory, music_uow_factory)
    group_list_query = GroupListQuery(music_uow_factory)
    group_overview_query = GroupOverviewQuery(music_uow_factory, people_uow_factory)
    lyrics_projection = LyricsVersionProjectionService(music_uow_factory, hk_uow_factory)
    song_list_query = SongListQuery(music_uow_factory)
    song_overview_query = SongOverviewQuery(music_uow_factory, people_uow_factory, hk_uow_factory, lyrics_projection)
    recording_list_query = RecordingListQuery(music_uow_factory, people_uow_factory)
    recording_overview_query = RecordingOverviewQuery(
        music_uow_factory, people_uow_factory, hk_uow_factory, lyrics_projection
    )
    claim_service = ClaimService(lambda: knowledge_music_scope(session_factory))
    recording_origin_claim_service = RecordingOriginClaimService(lambda: knowledge_music_scope(session_factory))
    source_service = SourceService(hk_uow_factory)
    group_service = GroupService(music_uow_factory)
    group_membership_service = GroupMembershipService(music_uow_factory)
    relations_query = GenreRelationsQuery(music_uow_factory, claim_service)
    sources_query = GenreSourcesQuery(music_uow_factory, claim_service, source_service)

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
        GROUP_SERVICE_DEPENDENCY: Provide(lambda: group_service, sync_to_thread=False),
        GROUP_MEMBERSHIP_SERVICE_DEPENDENCY: Provide(lambda: group_membership_service, sync_to_thread=False),
        RECORDING_ORIGIN_CLAIM_SERVICE_DEPENDENCY: Provide(
            lambda: recording_origin_claim_service,
            sync_to_thread=False,
        ),
    }
    if overrides is not None:
        dependencies.update(overrides)
    return dependencies
