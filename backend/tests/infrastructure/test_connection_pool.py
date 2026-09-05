"""Integration tests for the async SQLAlchemy connection pool behaviour."""

from asyncio import gather
from contextlib import asynccontextmanager
from os import environ
from time import perf_counter
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine


pytestmark = pytest.mark.integration


@asynccontextmanager
async def _small_pool_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        environ["TEST_DATABASE_URL"],
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
        pool_timeout=10,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_excess_requests_wait_for_available_connection_and_do_not_fail() -> None:
    """Concurrent queries beyond the pool are queued, not rejected.

    With pool_size=1/max_overflow=0 and 6 concurrent pg_sleep(0.05) calls,
    the requests serialize on the single connection and all succeed (no
    TimeoutError). Elapsed wall time proves queuing instead of failure or
    parallel execution.
    """

    async def ping() -> None:
        async with factory() as session:
            await session.execute(text("SELECT pg_sleep(0.05)"))

    async with _small_pool_engine() as engine:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        start = perf_counter()
        await gather(*(ping() for _ in range(6)))
        elapsed = perf_counter() - start

    # 6 serialized 50ms sleeps take >= ~0.30s; parallel would be <= ~0.1s.
    assert elapsed >= 0.25
