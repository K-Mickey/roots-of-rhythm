from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    GeographicContextView,
    HistoricalPeriodView,
    TemporalBoundView,
)
from roots_of_rhythm.discovery.application.dto.genres import (
    GenreOverviewResponse,
)
from roots_of_rhythm.discovery.application.errors.genres import (
    GenreOverviewAssemblyError,
    GenreOverviewNotFound,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.music_catalog.domain import GeographicContext, HistoricalPeriod

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
        start=TemporalBoundView.from_bound(period.start),
        end=TemporalBoundView.from_bound(period.end),
    )


def _map_geography(geography: GeographicContext | None) -> GeographicContextView | None:
    if geography is None:
        return None
    return GeographicContextView(summary=geography.summary)
