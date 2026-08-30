from typing import TYPE_CHECKING

import msgspec

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    GroupSummary,
    PublicImageView,
    TemporalBoundView,
)

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import ExistencePeriod


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
