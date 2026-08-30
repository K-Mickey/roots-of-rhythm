from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.genres import (
    GenreOverviewAssemblyError,
    GenreOverviewNotFound,
)
from roots_of_rhythm.discovery.application.genre_overview import GenreOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    ClassificationContent,
    EditorialStatus,
    Genre,
    GeographicContext,
    HistoricalPeriod,
    TemporalBound,
    TemporalPrecision,
)
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork


def _published_swing() -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(
            "Swing",
            definition="Jazz dance music of the Swing Era.",
            period=HistoricalPeriod.create(
                "1930s–1940s",
                TemporalBound(1930, TemporalPrecision.DECADE),
                TemporalBound(1940, TemporalPrecision.DECADE),
            ),
            geography=GeographicContext.create("United States"),
            historical_context="Big bands and dance halls.",
            formation="Developed within jazz.",
            characteristic_features=("Swing pulse", "Section arranging"),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_overview_query_returns_published_projection() -> None:
    genre = _published_swing()
    query = GenreOverviewQuery(lambda: FakeMusicCatalogUnitOfWork({genre.id: genre}))

    response = await query.get(genre.id)

    assert response.id == str(genre.id)
    assert response.name == "Swing"
    assert response.definition == "Jazz dance music of the Swing Era."
    assert response.primary_image is None
    assert response.period is not None
    assert response.period.label == "1930s–1940s"
    assert response.period.start is not None
    assert response.period.start.year == 1930
    assert response.period.start.precision == "decade"
    assert response.period.end is not None
    assert response.period.end.year == 1940
    assert response.period.end.precision == "decade"
    assert response.geography_or_origin is not None
    assert response.geography_or_origin.summary == "United States"
    assert response.historical_context == "Big bands and dance halls."
    assert response.formation == "Developed within jazz."
    assert response.characteristic_features == ["Swing pulse", "Section arranging"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, EditorialStatus.DRAFT, EditorialStatus.ARCHIVED])
async def test_overview_query_hides_missing_and_non_public_genres(status: EditorialStatus | None) -> None:
    genre_id = uuid7()
    genres = (
        {}
        if status is None
        else {
            genre_id: Genre(
                id=genre_id,
                content=ClassificationContent.create("Hidden", definition="Not public"),
                editorial_status=status,
            )
        }
    )
    query = GenreOverviewQuery(lambda: FakeMusicCatalogUnitOfWork(genres))

    with pytest.raises(GenreOverviewNotFound):
        await query.get(genre_id)


@pytest.mark.asyncio
async def test_overview_query_raises_assembly_error_without_definition() -> None:
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Broken"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    query = GenreOverviewQuery(lambda: FakeMusicCatalogUnitOfWork({genre.id: genre}))

    with pytest.raises(GenreOverviewAssemblyError):
        await query.get(genre.id)
