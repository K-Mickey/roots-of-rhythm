from typing import Literal

import msgspec

type TemporalPrecisionValue = Literal[
    "exact_year",
    "circa_year",
    "decade",
    "early_decade",
    "mid_decade",
    "late_decade",
]


class TemporalBoundView(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecisionValue


class HistoricalPeriodView(msgspec.Struct, frozen=True):
    label: str
    start: TemporalBoundView | None
    end: TemporalBoundView | None


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
