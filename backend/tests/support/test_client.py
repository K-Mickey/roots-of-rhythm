from os import environ
from typing import TYPE_CHECKING

from litestar.testing import TestClient

from roots_of_rhythm.config import PGSettings, Settings
from roots_of_rhythm.entrypoints.api import create_app
from tests.support.postgres import create_test_pg_settings

if TYPE_CHECKING:
    from typing import Mapping

    from litestar import Litestar
    from litestar.di import Provide


def create_missing_client(dependency_overrides: Mapping[str, Provide] | None = None) -> TestClient[Litestar]:
    settings = Settings(database_url="postgresql+asyncpg://roots:roots@127.0.0.1:1/missing")
    db_settings = PGSettings(
        database="missing",
        host="127.0.0.1",
        port=1,
        username="roots",
        password="roots",  # noqa: S106
    )
    return TestClient(
        app=create_app(
            settings=settings,
            db_settings=db_settings,
            dependency_overrides=dependency_overrides,
            middleware_overrides=[],
        ),
        raise_server_exceptions=True,
    )


def create_client(dependency_overrides: Mapping[str, Provide] | None = None) -> TestClient[Litestar]:
    settings = Settings(database_url=environ["TEST_DATABASE_URL"])
    db_settings = create_test_pg_settings()
    return TestClient(
        app=create_app(
            settings=settings,
            db_settings=db_settings,
            dependency_overrides=dependency_overrides,
        )
    )
