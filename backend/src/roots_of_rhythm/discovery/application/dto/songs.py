from typing import TYPE_CHECKING

import msgspec

from roots_of_rhythm.discovery.application.dto.common import (
    ExternalIdentityView,
    GenreSummary,
    PerformerSummary,
    SongSummary,
    TemporalBoundView,
)
from roots_of_rhythm.music_catalog.domain import (
    ExistencePeriod,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionRelationType,
    RecordingWorkUsageKind,
    WorkCreditRole,
    WorkRelationType,
)

if TYPE_CHECKING:
    from roots_of_rhythm.discovery.application.dto.recordings import RecordingPrimaryCreditView


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
