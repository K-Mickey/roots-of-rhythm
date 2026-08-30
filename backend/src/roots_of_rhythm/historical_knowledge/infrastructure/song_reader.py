from collections.abc import Callable, Collection
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
from roots_of_rhythm.historical_knowledge.public.song_context_reader import SongHistoricalKnowledgeReadData

if TYPE_CHECKING:
    from uuid import UUID

type HistoricalKnowledgeUnitOfWorkFactory = Callable[[], HistoricalKnowledgeUnitOfWork]


class SqlAlchemySongHistoricalKnowledgeReader:
    def __init__(self, uow_factory: HistoricalKnowledgeUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_song_data(
        self,
        source_version_ids: Collection[UUID],
        recording_ids: Collection[UUID],
    ) -> SongHistoricalKnowledgeReadData:
        async with self._uow_factory() as uow:
            versions = {} if not source_version_ids else await uow.sources.get_versions_by_ids(source_version_ids)
            source_ids = {item.source_id for item in versions.values()}
            sources = {} if not source_ids else await uow.sources.get_sources_by_ids(source_ids)
            claims = (
                {}
                if not recording_ids
                else await uow.recording_origin_claims.list_supported_published_for_recordings(recording_ids)
            )
        return SongHistoricalKnowledgeReadData(
            tuple(
                (version_id, source.access_policy)
                for version_id, version in versions.items()
                if (source := sources.get(version.source_id)) is not None
            ),
            tuple(item for items in claims.values() for item in items),
        )
