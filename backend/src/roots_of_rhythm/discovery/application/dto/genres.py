import msgspec

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    GeographicContextView,
    HistoricalPeriodView,
    PublicImageView,
    RelationHistoricalPeriodView,
    RelationPerspective,
)
from roots_of_rhythm.historical_knowledge.domain import EvidenceRole, EvidenceStatus, RelationType


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
