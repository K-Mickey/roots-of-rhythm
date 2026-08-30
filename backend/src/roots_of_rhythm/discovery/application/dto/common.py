from enum import StrEnum

import msgspec

from roots_of_rhythm.historical_knowledge.domain import (
    TemporalPrecision as HkTemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import (
    TemporalBound,
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


class GenreSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class PerformerSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class GroupSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class SongSummary(msgspec.Struct, frozen=True):
    id: str
    name: str


class PersonDateView(msgspec.Struct, frozen=True):
    year: int
    precision: PersonTemporalPrecision


class ExternalIdentityView(msgspec.Struct, frozen=True):
    provider: str
    identifier: str
    url: str | None
