from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import ListeningGuide


class StubListeningGuideRepository:
    def __init__(self, guides: dict[UUID, ListeningGuide] | None = None) -> None:
        self.guides = guides or {}
        self.locked_ids: list[UUID] = []

    async def add(self, guide: ListeningGuide) -> None:
        self.guides[guide.id] = guide

    async def get(self, guide_id: UUID, *, for_update: bool = False) -> ListeningGuide | None:
        if for_update:
            self.locked_ids.append(guide_id)
        return self.guides.get(guide_id)

    async def get_published_for_recording(self, recording_id: UUID) -> ListeningGuide | None:
        return next(
            (guide for guide in self.guides.values() if guide.recording_id == recording_id and guide.is_published),
            None,
        )

    async def save(self, guide: ListeningGuide) -> None:
        self.guides[guide.id] = guide

    async def mark_deleted(self, guide_id: UUID) -> None:
        self.guides.pop(guide_id, None)
