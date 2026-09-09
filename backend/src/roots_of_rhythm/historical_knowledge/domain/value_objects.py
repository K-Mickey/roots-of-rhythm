from uuid import UUID

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import EvidenceRole, TemporalPrecision
from roots_of_rhythm.historical_knowledge.domain.errors import HistoricalKnowledgeDomainError
from roots_of_rhythm.utils.text import optional_text, required_text
from roots_of_rhythm.utils.text_lengths import TEXT_64, TEXT_1024, TEXT_2048


def _replacement[T](current: T | None, replacement: T | None, *, clear: bool) -> T | None:
    if clear:
        return None
    return current if replacement is None else replacement


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
            label=required_text(label, "period label", max_length=TEXT_64, error=HistoricalKnowledgeDomainError),
            start=start,
            end=end,
        )


class GeographicContext(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "GeographicContext":
        return cls(
            summary=required_text(
                summary, "geographic summary", max_length=TEXT_64, error=HistoricalKnowledgeDomainError
            )
        )


class ClaimProvenance(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "ClaimProvenance":
        return cls(
            summary=required_text(
                summary, "provenance summary", max_length=TEXT_1024, error=HistoricalKnowledgeDomainError
            )
        )


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
            locator_text=optional_text(
                locator_text, "locator text", max_length=TEXT_1024, error=HistoricalKnowledgeDomainError
            ),
            external_url=optional_text(
                external_url, "external url", max_length=TEXT_2048, error=HistoricalKnowledgeDomainError
            ),
        )

    @property
    def is_supports(self) -> bool:
        return self.role is EvidenceRole.SUPPORTS

    @property
    def is_opposes(self) -> bool:
        return self.role is EvidenceRole.OPPOSES
