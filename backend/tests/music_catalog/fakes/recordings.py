from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Recording


class FakeRecordingRepository:
    def __init__(self, recordings: dict[UUID, Recording]) -> None:
        self._recordings = recordings
        self.locked_ids: list[UUID] = []

    async def add(self, recording: Recording) -> None:
        self._recordings[recording.id] = recording

    async def get(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        if for_update:
            self.locked_ids.append(recording_id)
        return self._recordings.get(recording_id)

    async def get_published(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        recording = await self.get(recording_id, for_update=for_update)
        if recording is None or not recording.is_published:
            return None
        return recording

    async def list_published(self) -> list[Recording]:
        return sorted(
            (recording for recording in self._recordings.values() if recording.is_published),
            key=lambda recording: (recording.title.casefold(), str(recording.id)),
        )

    async def list_published_for_work(self, work_id: UUID) -> list[Recording]:
        return sorted(
            (
                recording
                for recording in self._recordings.values()
                if recording.is_published and any(usage.work_id == work_id for usage in recording.work_usages)
            ),
            key=lambda recording: (recording.title.casefold(), str(recording.id)),
        )

    async def save(self, recording: Recording) -> None:
        if recording.id not in self._recordings:
            raise LookupError(str(recording.id))
        self._recordings[recording.id] = recording

    async def save_status(self, recording: Recording) -> None:
        if recording.id not in self._recordings:
            raise LookupError(str(recording.id))
        self._recordings[recording.id] = recording

    async def mark_deleted(self, recording_id: UUID) -> None:
        self._recordings.pop(recording_id, None)
