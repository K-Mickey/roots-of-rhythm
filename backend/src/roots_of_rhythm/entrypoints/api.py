from collections.abc import AsyncIterator  # noqa: TC003 - keep annotations explicit without TYPE_CHECKING indirection
from contextlib import asynccontextmanager

from litestar import Litestar
from sqlalchemy.exc import SQLAlchemyError

from roots_of_rhythm.config import Settings
from roots_of_rhythm.config import settings as default_settings
from roots_of_rhythm.discovery.presentation.genres import create_genres_router
from roots_of_rhythm.discovery.presentation.groups import create_groups_router
from roots_of_rhythm.discovery.presentation.performers import create_performers_router
from roots_of_rhythm.discovery.presentation.recordings import create_recordings_router
from roots_of_rhythm.discovery.presentation.songs import create_songs_router
from roots_of_rhythm.entrypoints.dependencies import DependencyProviders, create_api_dependencies
from roots_of_rhythm.infrastructure.database import (
    check_database_readiness,
    create_database_engine,
    create_session_factory,
)
from roots_of_rhythm.presentation.health import create_health_router


def create_app(
    settings: Settings | None = None,
    *,
    dependency_overrides: DependencyProviders | None = None,
) -> Litestar:
    resolved_settings = settings or default_settings
    engine = create_database_engine(resolved_settings.database_url)
    session_factory = create_session_factory(engine)

    async def readiness_probe() -> bool:
        try:
            await check_database_readiness(engine)
        except SQLAlchemyError:
            return False
        return True

    @asynccontextmanager
    async def database_lifespan(_: Litestar) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await engine.dispose()

    return Litestar(
        route_handlers=[
            create_health_router(readiness_probe),
            create_genres_router(),
            create_performers_router(),
            create_groups_router(),
            create_songs_router(),
            create_recordings_router(),
        ],
        dependencies=create_api_dependencies(session_factory, dependency_overrides),
        lifespan=[database_lifespan],
    )
