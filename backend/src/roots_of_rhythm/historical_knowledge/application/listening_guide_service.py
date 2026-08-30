from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.domain import ListeningGuide, ListeningObservation

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
    from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork

type ScopeFactory = Callable[[], AbstractAsyncContextManager[tuple[HistoricalKnowledgeUnitOfWork, RecordingUnitOfWork]]]


class ListeningGuideNotFound(LookupError):
    pass


class ListeningGuideRecordingNotPublished(ValueError):
    pass


class ListeningGuideService:
    def __init__(self, scope_factory: ScopeFactory) -> None:
        self._scope_factory = scope_factory

    async def create_draft(
        self,
        recording_id: UUID,
        observations: tuple[ListeningObservation, ...] = (),
        *,
        guide_id: UUID | None = None,
    ) -> ListeningGuide:
        guide = ListeningGuide.create_draft(recording_id, observations, guide_id=guide_id)
        async with self._scope_factory() as (hk, _music):
            await hk.listening_guides.add(guide)
            await hk.commit()
        return guide

    async def replace_observations(
        self, guide_id: UUID, observations: tuple[ListeningObservation, ...]
    ) -> ListeningGuide:
        async with self._scope_factory() as (hk, music):
            guide = await self._get(hk, guide_id)
            updated = guide.replace_observations(observations)
            if updated.editorial_status.value == "published":
                await self._require_recording(music, guide.recording_id)
            await hk.listening_guides.save(updated)
            await hk.commit()
        return updated

    async def publish(self, guide_id: UUID) -> ListeningGuide:
        async with self._scope_factory() as (hk, music):
            guide = await self._get(hk, guide_id)
            await self._require_recording(music, guide.recording_id)
            published = guide.publish()
            await hk.listening_guides.save(published)
            await hk.commit()
        return published

    async def archive(self, guide_id: UUID) -> ListeningGuide:
        async with self._scope_factory() as (hk, _music):
            guide = await self._get(hk, guide_id)
            archived = guide.archive()
            await hk.listening_guides.save(archived)
            await hk.commit()
        return archived

    @staticmethod
    async def _get(hk: HistoricalKnowledgeUnitOfWork, guide_id: UUID) -> ListeningGuide:
        guide = await hk.listening_guides.get(guide_id, for_update=True)
        if guide is None:
            raise ListeningGuideNotFound(str(guide_id))
        return guide

    @staticmethod
    async def _require_recording(music: RecordingUnitOfWork, recording_id: UUID) -> None:
        if await music.recordings.get_published(recording_id, for_update=True) is None:
            raise ListeningGuideRecordingNotPublished(str(recording_id))
