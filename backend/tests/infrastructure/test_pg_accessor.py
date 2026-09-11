import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from roots_of_rhythm.infrastructure.base import PgConfig
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.infrastructure.session_scope import SessionScope
from tests.support.postgres import close_leaked_pg_request_scope


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def create_session_maker(
    *,
    side_effect: object = None,
) -> Mock:
    maker = Mock(spec=async_sessionmaker)
    maker.return_value = AsyncMock(spec=AsyncSession)
    maker.side_effect = side_effect
    return maker


def _make_scope(main_session: AsyncSession, ro_session_maker: async_sessionmaker[AsyncSession]) -> SessionScope:
    return SessionScope(
        main_task=asyncio.current_task(),
        main_session=main_session,
        ro_session_maker=ro_session_maker,
        warn_threshold=10,
    )


async def test_get_current_session_returns_main_session_in_main_task(session: AsyncMock) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    scope = _make_scope(session, create_session_maker())

    token = pg._current_scope.set(scope)
    try:
        assert pg.get_current_session() is session
    finally:
        pg._current_scope.reset(token)


async def test_get_current_session_from_child_task_does_not_materialize_ro_session(session: AsyncMock) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    session_maker = create_session_maker(
        side_effect=AssertionError("probe-вызов get_current_session не должен создавать child-сессию")
    )
    scope = _make_scope(session, session_maker)

    async def child_probe() -> AsyncSession | None:
        return pg.get_current_session()

    token = pg._current_scope.set(scope)
    try:
        (result,) = await asyncio.gather(child_probe())
    finally:
        pg._current_scope.reset(token)

    assert result is None


async def test_get_current_session_returns_existing_child_session_without_creating_new(
    session: AsyncMock,
) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    session_maker = create_session_maker()
    scope = _make_scope(session, session_maker)

    async def child() -> tuple[object, object | None]:
        materialized = scope.get()
        peeked = pg.get_current_session()
        return materialized, peeked

    token = pg._current_scope.set(scope)
    try:
        ((materialized, peeked),) = await asyncio.gather(child())
    finally:
        pg._current_scope.reset(token)

    assert peeked is materialized
    assert session_maker.call_count == 1


async def test_new_session_from_child_task_raises(session: AsyncMock) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    scope = _make_scope(session, create_session_maker())

    async def child() -> None:
        async with pg.new_session():
            pass

    token = pg._current_scope.set(scope)
    try:
        with pytest.raises(RuntimeError, match="child task"):
            await asyncio.gather(child())
    finally:
        pg._current_scope.reset(token)


async def test_execute_with_main_session_from_child_task_raises(session: AsyncMock) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    scope = _make_scope(session, create_session_maker())

    async def child() -> None:
        await pg.execute(object(), session=session)

    token = pg._current_scope.set(scope)
    try:
        with pytest.raises(RuntimeError, match="does not own it"):
            await asyncio.gather(child())
    finally:
        pg._current_scope.reset(token)


async def test_execute_with_foreign_child_session_from_child_task_raises(
    session: AsyncMock,
) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    scope = _make_scope(session, create_session_maker())

    a_registered = asyncio.Event()
    b_done = asyncio.Event()
    captured: dict[str, AsyncSession] = {}

    async def child_a() -> None:
        captured["session"] = scope.get()
        a_registered.set()
        await b_done.wait()

    async def child_b() -> None:
        await a_registered.wait()
        try:
            with pytest.raises(RuntimeError, match="does not own it"):
                await pg.execute(object(), session=captured["session"])
        finally:
            b_done.set()

    token = pg._current_scope.set(scope)
    try:
        await asyncio.gather(child_a(), child_b())
    finally:
        pg._current_scope.reset(token)


async def test_connect_disposes_engines_when_validation_fails() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    created: list[Mock] = []

    def fake_create_engine(*, pool_size: int, max_overflow: int) -> Mock:
        engine = Mock(spec=AsyncEngine)
        connection = AsyncMock()
        connection.__aenter__.return_value = connection
        connection.execute.side_effect = ValueError("connect validation boom")
        engine.connect.return_value = connection
        created.append(engine)
        return engine

    pg._create_engine = fake_create_engine  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="connect validation boom"):
        await pg._connect()

    assert len(created) == 2
    assert all(engine.dispose.await_count == 1 for engine in created)
    assert pg._engine is None
    assert pg._ro_engine is None


async def test_new_session_at_request_boundary_ignores_scope_inherited_from_another_task() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    pg._session_maker = create_session_maker()
    pg._ro_session_maker = create_session_maker()

    async def next_pipelined_request() -> None:
        pg.reset_request_scope()
        async with pg.new_session():
            assert pg.get_current_session() is not None

    async with pg.new_session():
        # Как uvicorn при pipelining: таска следующего запроса — из контекста текущего.
        await asyncio.create_task(next_pipelined_request())


async def test_close_leaked_pg_request_scope_rolls_back_and_closes_main_session(
    session: AsyncMock,
) -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    pg._current_scope.set(_make_scope(session, create_session_maker()))

    await close_leaked_pg_request_scope(pg)

    assert pg.get_current_session() is None
    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


async def test_new_session_from_child_task_of_live_scope_still_raises() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    pg._session_maker = create_session_maker()
    pg._ro_session_maker = create_session_maker()

    async def gather_branch() -> None:
        async with pg.new_session():
            pass

    async with pg.new_session():
        with pytest.raises(RuntimeError, match="child task of an active request scope"):
            await asyncio.gather(gather_branch())
