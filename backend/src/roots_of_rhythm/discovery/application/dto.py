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
    BillingRole,
    ExistencePeriod,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionRelationType,
    RecordingContributionKind,
    RecordingCreditTargetKind,
    RecordingWorkUsageKind,
    TemporalBound,
    WorkCreditRole,
    WorkRelationType,
)
from roots_of_rhythm.music_catalog.domain import (
    TemporalPrecision as McTemporalPrecision,
)
from roots_of_rhythm.people_catalog.domain import TemporalPrecision as PersonTemporalPrecision


class RelationPerspective(StrEnum):
    SUBJECT = "subject"
    TARGET = "target"
    SYMMETRIC = "symmetric"


class TemporalBoundView(msgspec.Struct, frozen=True):
    year: int
    precision: McTemporalPrecision

    @classmethod
    def from_bound(cls, bound: TemporalBound | None) -> "TemporalBoundView | None":
        if bound is None:
            return None
        return cls(year=bound.year, precision=bound.precision)


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


class PerformerSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class PerformerListResponse(msgspec.Struct, frozen=True):
    items: list[PerformerSummary]


class GroupSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class GroupListResponse(msgspec.Struct, frozen=True):
    items: list[GroupSummary]


class GroupPeriodView(msgspec.Struct, frozen=True):
    start: TemporalBoundView | None
    end: TemporalBoundView | None

    @classmethod
    def from_period(cls, period: ExistencePeriod | None) -> "GroupPeriodView":
        if period is None:
            return cls(start=None, end=None)
        return cls(
            start=TemporalBoundView.from_bound(period.start),
            end=TemporalBoundView.from_bound(period.end),
        )


class GroupMemberView(msgspec.Struct, frozen=True):
    id: str
    name: str
    period: GroupPeriodView
    roles_or_instruments: list[str]


class GroupOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    name: str
    aliases: list[str]
    description: str | None
    period: GroupPeriodView
    primary_image: PublicImageView | None
    genres: list[GenreSummary]
    members: list[GroupMemberView]


class SongSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class SongListResponse(msgspec.Struct, frozen=True):
    items: list[SongSummary]


class SongPeriodView(msgspec.Struct, frozen=True):
    start: TemporalBoundView | None
    end: TemporalBoundView | None

    @classmethod
    def from_period(cls, period: ExistencePeriod | None) -> "SongPeriodView":
        if period is None:
            return cls(start=None, end=None)
        return cls(
            start=TemporalBoundView.from_bound(period.start),
            end=TemporalBoundView.from_bound(period.end),
        )


class SongWorkCreditView(msgspec.Struct, frozen=True):
    person: PerformerSummary
    role: WorkCreditRole
    credited_as: str | None


class RelatedWorkView(msgspec.Struct, frozen=True):
    relation_type: WorkRelationType
    work: SongSummary


class LyricsVersionSummary(msgspec.Struct, frozen=True):
    id: str
    language_tag: str
    label: str | None


class LyricsVersionRelationView(msgspec.Struct, frozen=True):
    relation_type: LyricsVersionRelationType
    version: LyricsVersionSummary


class SongLyricsVersionView(msgspec.Struct, frozen=True):
    id: str
    language_tag: str
    label: str | None
    usage_kind: LyricsUsageKind
    creation_method: LyricsCreationMethod
    body: str | None
    body_unavailable_reason: str | None
    credits: list[SongWorkCreditView]
    relations: list[LyricsVersionRelationView]


class PersonDateView(msgspec.Struct, frozen=True):
    year: int
    precision: PersonTemporalPrecision


class ExternalIdentityView(msgspec.Struct, frozen=True):
    provider: str
    identifier: str
    url: str | None


class SongOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    name: str
    aliases: list[str]
    description: str | None
    period: SongPeriodView
    external_identities: list[ExternalIdentityView]
    credits: list[SongWorkCreditView]
    classifications: list[GenreSummary]
    related_works: list[RelatedWorkView]
    lyrics_versions: list[SongLyricsVersionView]
    recording_genres: list["SongRecordingGenreFacet"]
    recordings: list["SongRecordingSummary"]


class SongRecordingGenreFacet(msgspec.Struct, frozen=True):
    genre: GenreSummary
    recording_count: int


class SongRecordingSummary(msgspec.Struct, frozen=True):
    id: str
    title: str
    recorded_period: SongPeriodView
    first_release_date: None
    primary_credits: list["RecordingPrimaryCreditView"]
    genre_ids: list[str]
    work_usage_kind: RecordingWorkUsageKind
    origin_badges: list[str]


class RecordingWorkView(msgspec.Struct, frozen=True):
    work: SongSummary
    usage_kind: RecordingWorkUsageKind
    position: int | None


class RecordingCreditView(msgspec.Struct, frozen=True):
    target_kind: RecordingCreditTargetKind
    target: PerformerSummary | GroupSummary
    billing_role: BillingRole
    contribution_kind: RecordingContributionKind | None
    instrument: str | None
    credited_as: str | None


class RecordingLyricsVersionView(msgspec.Struct, frozen=True):
    id: str
    language_tag: str
    label: str | None
    creation_method: LyricsCreationMethod
    body: str | None
    body_unavailable_reason: str | None
    position: int | None
    confirmed_for_recording: bool


class ListeningObservationView(msgspec.Struct, frozen=True):
    feature: str
    explanation: str
    context: str | None
    position: int
    start_seconds: int | None
    end_seconds: int | None


class ListeningGuideView(msgspec.Struct, frozen=True):
    observations: list[ListeningObservationView]


class RecordingPrimaryCreditView(msgspec.Struct, frozen=True):
    target_kind: RecordingCreditTargetKind
    target: PerformerSummary | GroupSummary


class RecordingListItem(msgspec.Struct, frozen=True):
    id: str
    title: str
    period: SongPeriodView
    primary_credits: list[RecordingPrimaryCreditView]
    genres: list[GenreSummary]


class RecordingListResponse(msgspec.Struct, frozen=True):
    items: list[RecordingListItem]


class RecordingOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    title: str
    period: SongPeriodView
    description: str | None
    isrc: str | None
    first_release_date: None
    works: list[RecordingWorkView]
    credits: list[RecordingCreditView]
    genres: list[GenreSummary]
    lyrics: list[RecordingLyricsVersionView]
    listening_guide: ListeningGuideView | None
    origin_badges: list[str]


class PerformerOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    name: str
    aliases: list[str]
    biography: str | None
    birth_date: PersonDateView | None
    death_date: PersonDateView | None
    external_identities: list[ExternalIdentityView]
    primary_image: PublicImageView | None
    genres: list[GenreSummary]


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
