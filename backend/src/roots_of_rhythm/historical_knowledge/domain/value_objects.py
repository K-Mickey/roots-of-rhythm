from uuid import UUID

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import EvidenceRole, RelationType, TemporalPrecision
from roots_of_rhythm.historical_knowledge.domain.errors import HistoricalKnowledgeDomainError

SHORT_TEXT_MAX_LENGTH = 64
LONG_TEXT_MAX_LENGTH = 1024
URL_MAX_LENGTH = 2048


def _required_text(value: str, field: str, *, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise HistoricalKnowledgeDomainError(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise HistoricalKnowledgeDomainError(f"{field} must be at most {max_length} characters")
    return normalized


def _optional_text(value: str | None, field: str, *, max_length: int) -> str | None:
    return None if value is None else _required_text(value, field, max_length=max_length)


class TemporalBound(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecision


class HistoricalPeriod(msgspec.Struct, frozen=True):
    label: str
    start: TemporalBound | None = None
    end: TemporalBound | None = None

    @classmethod
    def create(
        cls,
        label: str,
        start: TemporalBound | None = None,
        end: TemporalBound | None = None,
    ) -> "HistoricalPeriod":
        if start is not None and end is not None and start.year > end.year:
            raise HistoricalKnowledgeDomainError("period start must not be later than period end")
        return cls(
            label=_required_text(label, "period label", max_length=SHORT_TEXT_MAX_LENGTH),
            start=start,
            end=end,
        )


class GeographicContext(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "GeographicContext":
        return cls(summary=_required_text(summary, "geographic summary", max_length=SHORT_TEXT_MAX_LENGTH))


class ClaimProvenance(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "ClaimProvenance":
        return cls(summary=_required_text(summary, "provenance summary", max_length=LONG_TEXT_MAX_LENGTH))


class ClaimEvidenceReference(msgspec.Struct, frozen=True):
    source_fragment_id: UUID
    role: EvidenceRole
    locator_text: str | None = None
    external_url: str | None = None

    @classmethod
    def create(
        cls,
        source_fragment_id: UUID,
        role: EvidenceRole,
        *,
        locator_text: str | None = None,
        external_url: str | None = None,
    ) -> "ClaimEvidenceReference":
        return cls(
            source_fragment_id=source_fragment_id,
            role=role,
            locator_text=_optional_text(locator_text, "locator text", max_length=LONG_TEXT_MAX_LENGTH),
            external_url=_optional_text(external_url, "external url", max_length=URL_MAX_LENGTH),
        )


def canonicalize_relation_endpoints(
    subject_genre_id: UUID,
    target_genre_id: UUID,
    relation_type: RelationType,
) -> tuple[UUID, UUID]:
    if subject_genre_id == target_genre_id:
        raise HistoricalKnowledgeDomainError("subject and target Genre IDs must be distinct")
    if relation_type is RelationType.OVERLAPS_WITH and subject_genre_id.int > target_genre_id.int:
        return target_genre_id, subject_genre_id
    return subject_genre_id, target_genre_id
