from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus
from roots_of_rhythm.music_catalog.domain.errors import RecordingPublicationError
from roots_of_rhythm.music_catalog.domain.value_objects import (
    ExistencePeriod,
    RecordingContent,
    RecordingCredit,
    RecordingLyricsUsage,
    RecordingWorkUsage,
)


class Recording(msgspec.Struct, frozen=True):
    id: UUID
    title: str
    recorded_period: ExistencePeriod | None = None
    description: str | None = None
    isrc: str | None = None
    credits: tuple[RecordingCredit, ...] = ()
    work_usages: tuple[RecordingWorkUsage, ...] = ()
    lyrics_usages: tuple[RecordingLyricsUsage, ...] = ()
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        recording_id: UUID,
        content: RecordingContent,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "Recording":
        return cls(
            id=recording_id,
            title=content.title,
            recorded_period=content.recorded_period,
            description=content.description,
            isrc=content.isrc,
            credits=content.credits,
            work_usages=content.work_usages,
            lyrics_usages=content.lyrics_usages,
            editorial_status=editorial_status,
        )

    @property
    def is_published(self) -> bool:
        return self.editorial_status is EditorialStatus.PUBLISHED

    @property
    def is_draft(self) -> bool:
        return self.editorial_status is EditorialStatus.DRAFT

    def replace_content(self, content: RecordingContent) -> "Recording":
        updated = Recording.create(self.id, content, editorial_status=self.editorial_status)
        return updated.publish() if self.is_published else updated

    def submit_for_review(self) -> "Recording":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "Recording":
        missing_fields: list[str] = []
        if not any(credit.is_primary_billing for credit in self.credits):
            missing_fields.append("primary_credit")
        if not self.work_usages:
            missing_fields.append("work_usage")
        if missing_fields:
            raise RecordingPublicationError(tuple(missing_fields))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "Recording":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "Recording":
        return Recording(
            id=self.id,
            title=self.title,
            recorded_period=self.recorded_period,
            description=self.description,
            isrc=self.isrc,
            credits=self.credits,
            work_usages=self.work_usages,
            lyrics_usages=self.lyrics_usages,
            editorial_status=status,
        )
