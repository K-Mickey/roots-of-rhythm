from collections.abc import Mapping
from typing import TYPE_CHECKING

from litestar.di import Provide

from roots_of_rhythm.discovery.application.genre_overview import GenreOverviewQuery
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

GENRE_OVERVIEW_READER_DEPENDENCY = "genre_overview_reader"

type DependencyProviders = Mapping[str, Provide]


def create_api_dependencies(
    session_factory: async_sessionmaker[AsyncSession],
    overrides: DependencyProviders | None = None,
) -> dict[str, Provide]:
    query = GenreOverviewQuery(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    dependencies = {
        GENRE_OVERVIEW_READER_DEPENDENCY: Provide(lambda: query, sync_to_thread=False),
    }
    if overrides is not None:
        dependencies.update(overrides)
    return dependencies
