from collections.abc import AsyncIterator  # noqa: TC003 - keep annotations explicit without TYPE_CHECKING indirection
from contextlib import asynccontextmanager

from litestar import Litestar
from sqlalchemy.exc import SQLAlchemyError

from roots_of_rhythm.config import Settings
from roots_of_rhythm.config import settings as default_settings
from roots_of_rhythm.infrastructure.database import check_database_readiness, create_database_engine
from roots_of_rhythm.presentation.health import create_health_router


def create_app(settings: Settings | None = None) -> Litestar:
    resolved_settings = settings or default_settings
    engine = create_database_engine(resolved_settings.database_url)

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
        route_handlers=[create_health_router(readiness_probe)],
        lifespan=[database_lifespan],
    )
