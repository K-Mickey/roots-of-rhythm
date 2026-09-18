import asyncio
from os import environ
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from sqlalchemy import delete

from roots_of_rhythm.infrastructure.database import create_database_engine
from roots_of_rhythm.infrastructure.models import BaseModel
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.infrastructure.uow import PgUnitOfWork
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.infrastructure.person_repository import PgPersonRepository
from tests.support.postgres import (
    close_leaked_pg_request_scope,
    connect_test_db,
    create_test_pg_config,
    run_migrations,
)
from tests.support.seed import run_corpus_seed
from tests.support.test_client import create_client

if TYPE_CHECKING:
    from typing import AsyncIterator

    from litestar import Litestar
    from litestar.testing import TestClient
    from sqlalchemy.ext.asyncio import AsyncEngine

    from roots_of_rhythm.application.ports import DbAccessor, UnitOfWork
    from roots_of_rhythm.people_catalog.application import PersonRepository
    from roots_of_rhythm.people_catalog.public import PeopleCatalog


@pytest.fixture
async def database() -> AsyncIterator[DbAccessor]:
    """Живой PgAccessor к тестовой БД (engine-параметр нужен для wipe-порядка)."""
    db = PgAccessor(create_test_pg_config())

    async def _connect() -> None:
        await connect_test_db(db)

    with patch.object(db, "_connect", _connect):
        await db.connect()

        await asyncio.to_thread(run_migrations, resolve_database_url())
        await _wipe_corpus(db.engine)

        try:
            yield db
        finally:
            await close_leaked_pg_request_scope(db)
            await db.disconnect()


@pytest.fixture
def uow(database: DbAccessor) -> UnitOfWork:
    return PgUnitOfWork(database)


@pytest.fixture
def person_repository(database: DbAccessor) -> PersonRepository:
    return PgPersonRepository(database)


@pytest.fixture
def person_service(uow: UnitOfWork, person_repository: PersonRepository) -> PeopleCatalog:
    return PersonService(uow, person_repository)


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_engine = create_database_engine(resolve_database_url())
    await _wipe_corpus(database_engine)
    yield database_engine
    await _wipe_corpus(database_engine)
    await database_engine.dispose()


async def _wipe_corpus(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        for table in reversed(BaseModel.metadata.sorted_tables):
            await connection.execute(delete(table))


def resolve_database_url() -> str:
    return environ["TEST_DATABASE_URL"]


@pytest.fixture
async def seeded_engine(engine: AsyncEngine, database: DbAccessor, uow: UnitOfWork) -> AsyncEngine:
    await run_corpus_seed(engine, database, uow)
    return engine


@pytest.fixture
async def seeded_client(engine: AsyncEngine, database: DbAccessor, uow: UnitOfWork) -> TestClient[Litestar]:
    await run_corpus_seed(engine, database, uow)
    return create_client()
