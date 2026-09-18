from collections.abc import AsyncIterator  # noqa: TC003 - keep annotations explicit without TYPE_CHECKING indirection
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from litestar import Litestar

from roots_of_rhythm.config import PGSettings, Settings, pg_settings
from roots_of_rhythm.config import settings as default_settings
from roots_of_rhythm.entrypoints.dependencies import DependencyProviders, create_api_dependencies
from roots_of_rhythm.infrastructure.base import create_pg_config
from roots_of_rhythm.infrastructure.database import (
    check_database_readiness,
    create_database_engine,
    create_session_factory,
)
from roots_of_rhythm.infrastructure.middlewares import PgSessionMiddleware
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.presentation.api_router import create_api_router
from roots_of_rhythm.presentation.health import create_health_router

if TYPE_CHECKING:
    from typing import Sequence

    from litestar.types import Middleware


def create_app(
    settings: Settings | None = None,
    db_settings: PGSettings | None = None,
    *,
    dependency_overrides: DependencyProviders | None = None,
    middleware_overrides: Sequence[Middleware] | None = None,
) -> Litestar:
    resolved_settings = settings or default_settings
    engine = create_database_engine(resolved_settings.database_url)
    session_factory = create_session_factory(engine)

    resolved_pg_settings = db_settings or pg_settings
    db_accessor = PgAccessor(config=create_pg_config(resolved_pg_settings))

    async def readiness_probe() -> bool:
        try:
            await check_database_readiness(engine)
        except Exception:  # noqa: BLE001
            return False
        return True

    @asynccontextmanager
    async def database_lifespan(_: Litestar) -> AsyncIterator[None]:
        try:
            await db_accessor.connect()
            yield
        finally:
            await engine.dispose()
            await db_accessor.disconnect()

    if middleware_overrides is not None:
        middleware = middleware_overrides
    else:
        api_prefixes = ("/api/v1",)
        middleware = [PgSessionMiddleware(database=db_accessor, prefixes=api_prefixes)]

    return Litestar(
        route_handlers=[
            create_health_router(readiness_probe),
            create_api_router(),
        ],
        dependencies=create_api_dependencies(
            db_accessor=db_accessor,
            session_factory=session_factory,
            overrides=dependency_overrides,
        ),
        lifespan=[database_lifespan],
        middleware=middleware,
        debug=resolved_settings.develop,
    )
