from enum import StrEnum

import msgspec

from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceRole,
    EvidenceStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.domain import (
    TemporalPrecision as HkTemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import (
    TemporalPrecision as McTemporalPrecision,
)


class RelationPerspective(StrEnum):
    SUBJECT = "subject"
    TARGET = "target"
    SYMMETRIC = "symmetric"


class TemporalBoundView(msgspec.Struct, frozen=True):
    year: int
    precision: McTemporalPrecision


class HistoricalPeriodView(msgspec.Struct, frozen=True):
    label: str
    start: TemporalBoundView | None
    end: TemporalBoundView | None


class RelationTemporalBoundView(msgspec.Struct, frozen=True):
    year: int
    precision: HkTemporalPrecision


class RelationHistoricalPeriodView(msgspec.Struct, frozen=True):
    label: str
    start: RelationTemporalBoundView | None
    end: RelationTemporalBoundView | None


class GeographicContextView(msgspec.Struct, frozen=True):
    summary: str


class PublicImageView(msgspec.Struct, frozen=True):
    id: str
    url: str
    alt_text: str
    width: int | None
    height: int | None
    attribution_text: str | None
    attribution_url: str | None


class GenreOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    name: str
    definition: str
    primary_image: PublicImageView | None
    period: HistoricalPeriodView | None
    geography_or_origin: GeographicContextView | None
    historical_context: str | None
    formation: str | None
    characteristic_features: list[str]


class GenreSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class GenreListResponse(msgspec.Struct, frozen=True):
    items: list[GenreSummary]


class EvidenceReferenceView(msgspec.Struct, frozen=True):
    source_id: str
    role: EvidenceRole
    locator_text: str | None
    external_url: str | None


class GenreRelationView(msgspec.Struct, frozen=True):
    id: str
    related_genre: GenreSummary
    relation_type: RelationType
    perspective: RelationPerspective
    explanation: str
    temporal_context: RelationHistoricalPeriodView | None
    geographic_context: GeographicContextView | None
    evidence_status: EvidenceStatus
    evidence_references: list[EvidenceReferenceView]


class GenreRelationsResponse(msgspec.Struct, frozen=True):
    genre_id: str
    relations: list[GenreRelationView]


class SourceView(msgspec.Struct, frozen=True):
    id: str
    title: str
    author: str | None
    responsible_organization: str | None
    publication: str | None
    publication_date: str | None
    external_url: str | None


class GenreSourcesResponse(msgspec.Struct, frozen=True):
    genre_id: str
    sources: list[SourceView]
