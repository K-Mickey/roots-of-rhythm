from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import (
    GenreOverviewResponse,
    GeographicContextView,
    HistoricalPeriodView,
    TemporalBoundView,
    TemporalPrecisionValue,
)
from roots_of_rhythm.discovery.application.errors import (
    GenreOverviewAssemblyError,
    GenreOverviewNotFound,
)
from roots_of_rhythm.music_catalog.domain.enums import TemporalPrecision

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.music_catalog.domain import Genre
    from roots_of_rhythm.music_catalog.domain.value_objects import GeographicContext, HistoricalPeriod, TemporalBound

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GenreOverviewReader(Protocol):
    async def get(self, genre_id: UUID) -> GenreOverviewResponse: ...


class GenreOverviewQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, genre_id: UUID) -> GenreOverviewResponse:
        async with self._uow_factory() as uow:
            genre = await uow.genres.get_published(genre_id)
        if genre is None:
            raise GenreOverviewNotFound(str(genre_id))
        return map_genre_overview(genre)


def map_genre_overview(genre: Genre) -> GenreOverviewResponse:
    definition = genre.content.definition
    if definition is None:
        raise GenreOverviewAssemblyError("published genre is missing definition")
    return GenreOverviewResponse(
        id=str(genre.id),
        name=genre.content.canonical_name,
        definition=definition,
        primary_image=None,
        period=_map_period(genre.content.period),
        geography_or_origin=_map_geography(genre.content.geography),
        historical_context=genre.content.historical_context,
        formation=genre.content.formation,
        characteristic_features=list(genre.content.characteristic_features),
    )


def _map_period(period: HistoricalPeriod | None) -> HistoricalPeriodView | None:
    if period is None:
        return None
    return HistoricalPeriodView(
        label=period.label,
        start=_map_bound(period.start),
        end=_map_bound(period.end),
    )


def _map_bound(bound: TemporalBound | None) -> TemporalBoundView | None:
    if bound is None:
        return None
    return TemporalBoundView(year=bound.year, precision=_map_precision(bound.precision))


def _map_precision(precision: TemporalPrecision) -> TemporalPrecisionValue:
    match precision:
        case TemporalPrecision.EXACT_YEAR:
            return "exact_year"
        case TemporalPrecision.CIRCA_YEAR:
            return "circa_year"
        case TemporalPrecision.DECADE:
            return "decade"
        case TemporalPrecision.EARLY_DECADE:
            return "early_decade"
        case TemporalPrecision.MID_DECADE:
            return "mid_decade"
        case TemporalPrecision.LATE_DECADE:
            return "late_decade"


def _map_geography(geography: GeographicContext | None) -> GeographicContextView | None:
    if geography is None:
        return None
    return GeographicContextView(summary=geography.summary)
