from datetime import datetime
from typing import Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import EditorialStatus
from roots_of_rhythm.historical_knowledge.domain.errors import HistoricalKnowledgeDomainError
from roots_of_rhythm.historical_knowledge.domain.value_objects import _required_text
from roots_of_rhythm.text_lengths import TEXT_64, TEXT_1024


class ListeningObservation(msgspec.Struct, frozen=True):
    id: UUID
    feature: str
    explanation: str
    author_id: UUID
    authored_at: datetime
    context: str | None = None
    start_seconds: int | None = None
    end_seconds: int | None = None
    position: int = 0

    @classmethod
    def create(
        cls,
        feature: str,
        explanation: str,
        author_id: UUID,
        authored_at: datetime,
        *,
        observation_id: UUID | None = None,
        context: str | None = None,
        start_seconds: int | None = None,
        end_seconds: int | None = None,
    ) -> Self:
        if (start_seconds is None) is not (end_seconds is None):
            raise HistoricalKnowledgeDomainError("listening range requires both bounds")
        if start_seconds is not None and (start_seconds < 0 or end_seconds is None or start_seconds >= end_seconds):
            raise HistoricalKnowledgeDomainError("listening range must satisfy 0 <= start < end")
        return cls(
            id=observation_id or uuid7(),
            feature=_required_text(feature, "feature", max_length=TEXT_64),
            explanation=_required_text(explanation, "explanation", max_length=TEXT_1024),
            author_id=author_id,
            authored_at=authored_at,
            context=None if context is None else _required_text(context, "context", max_length=TEXT_1024),
            start_seconds=start_seconds,
            end_seconds=end_seconds,
        )


class ListeningGuide(msgspec.Struct, frozen=True):
    id: UUID
    recording_id: UUID
    observations: tuple[ListeningObservation, ...] = ()
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create_draft(
        cls,
        recording_id: UUID,
        observations: tuple[ListeningObservation, ...] = (),
        *,
        guide_id: UUID | None = None,
    ) -> "ListeningGuide":
        return cls(id=guide_id or uuid7(), recording_id=recording_id, observations=_ordered(observations))

    def replace_observations(self, observations: tuple[ListeningObservation, ...]) -> "ListeningGuide":
        updated = ListeningGuide(self.id, self.recording_id, _ordered(observations), self.editorial_status)
        return updated.publish() if self.editorial_status is EditorialStatus.PUBLISHED else updated

    def submit_for_review(self) -> "ListeningGuide":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "ListeningGuide":
        if not self.observations:
            raise HistoricalKnowledgeDomainError("published listening guide requires an observation")
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "ListeningGuide":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "ListeningGuide":
        return ListeningGuide(self.id, self.recording_id, self.observations, status)


def _ordered(observations: tuple[ListeningObservation, ...]) -> tuple[ListeningObservation, ...]:
    ids = [item.id for item in observations]
    if len(ids) != len(set(ids)):
        raise HistoricalKnowledgeDomainError("listening observations must be unique")
    return tuple(
        ListeningObservation(
            item.id,
            item.feature,
            item.explanation,
            item.author_id,
            item.authored_at,
            item.context,
            item.start_seconds,
            item.end_seconds,
            position,
        )
        for position, item in enumerate(observations, start=1)
    )
