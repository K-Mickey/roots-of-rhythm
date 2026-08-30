import msgspec

from roots_of_rhythm.discovery.application.dto.common import GenreSummary, GroupSummary, PerformerSummary, SongSummary
from roots_of_rhythm.discovery.application.dto.songs import SongPeriodView
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    LyricsCreationMethod,
    RecordingContributionKind,
    RecordingCreditTargetKind,
    RecordingWorkUsageKind,
)


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
