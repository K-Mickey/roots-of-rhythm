import asyncio
import logging
from typing import TYPE_CHECKING, Any

import msgspec.structs
import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import QueuePool

from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.infrastructure.uow import PgUnitOfWork
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord
from roots_of_rhythm.people_catalog.infrastructure.person_repository import PgPersonRepository
from tests.people_catalog.support.helpers import create_person
from tests.support.waiting import wait_until_async

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from sqlalchemy.sql import Select

    from roots_of_rhythm.application.ports import DbAccessor
    from roots_of_rhythm.infrastructure.base import PgConfig
    from roots_of_rhythm.people_catalog.application import PersonRepository


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

GATHER_TIMEOUT_SECONDS = 15.0


def _select(sql: str) -> "Select[Any]":
    """SQL-выражение (без ключевого слова SELECT) в Select — scalar-хелперы типизированы под TypedReturnsRows."""
    return sa.select(text(sql))


@pytest.fixture
def person_repository(database: DbAccessor) -> PersonRepository:
    return PgPersonRepository(database)


def _checked_out_connections(accessor: DbAccessor, *, ro: bool = False) -> int:
    pool = (accessor.ro_engine if ro else accessor.engine).pool
    assert isinstance(pool, QueuePool)
    return pool.checkedout()


@pytest_asyncio.fixture(loop_scope="function")
async def make_pooled_pg(database: DbAccessor) -> "AsyncGenerator[Callable[..., Awaitable[DbAccessor]], None]":
    accessors: list[DbAccessor] = []

    async def factory(config: PgConfig | None = None) -> DbAccessor:
        accessor = PgAccessor(config=config or database.config)
        await accessor.connect()
        accessors.append(accessor)
        return accessor

    yield factory
    for accessor in accessors:
        await accessor.disconnect()


@pytest_asyncio.fixture(loop_scope="function")
async def pooled_pg(make_pooled_pg: "Callable[..., Awaitable[DbAccessor]]") -> DbAccessor:
    return await make_pooled_pg()


async def test_gather_on_request_session_does_not_share_connection(database: DbAccessor) -> None:
    async with database.new_session():
        results = await asyncio.wait_for(
            asyncio.gather(*[database.scalar(_select("pg_sleep(0.1)::text")) for _ in range(5)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
    assert len(results) == 5


async def test_gather_branches_use_own_connections(database: DbAccessor) -> None:
    async def branch_pids() -> tuple[int | None, int | None]:
        first: int | None = await database.scalar(_select("pg_backend_pid()"))
        second: int | None = await database.scalar(_select("pg_backend_pid()"))
        return first, second

    async with database.new_session():
        main_pid_before = await database.scalar(_select("pg_backend_pid()"))
        branches = await asyncio.wait_for(
            asyncio.gather(*[branch_pids() for _ in range(3)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
        main_pid_after = await database.scalar(_select("pg_backend_pid()"))

    assert main_pid_before == main_pid_after
    branch_pid_values = {pids[0] for pids in branches}
    for first, second in branches:
        assert first == second, "внутри одной ветки должна использоваться одна сессия"
    assert len(branch_pid_values) == 3, "ветки должны работать в разных соединениях"
    assert main_pid_before not in branch_pid_values, "ветки не должны делить соединение главной задачи"


async def test_child_branch_is_read_only(database: DbAccessor) -> None:
    async def write_branch() -> None:
        await database.execute(text("UPDATE persons SET biography = biography"))

    async with database.new_session():
        with pytest.raises(DBAPIError, match="read-only"):
            await asyncio.wait_for(
                asyncio.gather(write_branch()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_child_does_not_see_uncommitted_main_writes(
    database: DbAccessor,
    person_repository: PersonRepository,
) -> None:
    person = create_person("Sam")
    count_q = text("count(*) from persons where id = :id_")

    async def child_count() -> int | None:
        return await database.scalar(sa.select(count_q.bindparams(id_=person.id)))

    async with database.new_session():
        await person_repository.add(person)
        (child_visible,) = await asyncio.wait_for(
            asyncio.gather(child_count()),
            timeout=GATHER_TIMEOUT_SECONDS,
        )

    assert child_visible == 0, "ветка не должна видеть незакоммиченные записи главной сессии"
    assert await database.scalar(sa.select(count_q.bindparams(id_=person.id))) == 1, "после commit запись видна"


async def test_no_connection_leak_after_scope(pooled_pg: DbAccessor) -> None:
    async with pooled_pg.new_session():
        await asyncio.wait_for(
            asyncio.gather(*[pooled_pg.scalar(_select("pg_sleep(0.05)::text")) for _ in range(4)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )

    assert _checked_out_connections(pooled_pg) == 0
    assert _checked_out_connections(pooled_pg, ro=True) == 0


async def test_cancelled_siblings_do_not_leak(pooled_pg: DbAccessor) -> None:
    slow_ready = asyncio.Event()

    async def slow_branch() -> None:
        await pooled_pg.scalar(_select("1"))
        slow_ready.set()
        await pooled_pg.scalar(_select("pg_sleep(60)::text"))

    async def failing_branch() -> None:
        await slow_ready.wait()
        raise ValueError("boom")

    async with pooled_pg.new_session():
        with pytest.raises(ValueError, match="boom"):
            await asyncio.wait_for(
                asyncio.gather(slow_branch(), failing_branch()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )

    assert _checked_out_connections(pooled_pg) == 0
    assert _checked_out_connections(pooled_pg, ro=True) == 0
    assert await pooled_pg.scalar(_select("1")) == 1, "аксессор остаётся работоспособным"


async def test_child_dml_statement_raises(database: DbAccessor) -> None:
    async def write_branch() -> None:
        await database.execute(sa.update(PersonRecord).values(biography=PersonRecord.biography))

    async with database.new_session():
        with pytest.raises(RuntimeError, match="read-only child"):
            await asyncio.wait_for(
                asyncio.gather(write_branch()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_child_session_released_when_task_finishes(pooled_pg: DbAccessor) -> None:
    async with pooled_pg.new_session():
        await pooled_pg.scalar(_select("1"))  # основная сессия удерживает 1 rw-соединение
        await asyncio.wait_for(
            asyncio.gather(pooled_pg.scalar(_select("1"))),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
        # Закрытие child-сессии происходит в фоновой cleanup-задаче — даём ей выполниться.
        await wait_until_async(
            lambda: _checked_out_connections(pooled_pg, ro=True) == 0,
            interval_seconds=0.01,
            message="child-сессия должна вернуть соединение сразу после завершения своей задачи",
        )
        assert _checked_out_connections(pooled_pg) == 1, "основная сессия держит своё rw-соединение"


async def test_many_child_branches_do_not_exhaust_pool(pooled_pg: DbAccessor) -> None:
    # 40 веток > ro_pool_max_size (5) + ro_max_overflow (15): без освобождения соединений
    # по завершении задач это деградировало в circular wait и pool timeout.
    async with pooled_pg.new_session():
        results = await asyncio.wait_for(
            asyncio.gather(*[pooled_pg.scalar(_select("1")) for _ in range(40)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
    assert results == [1] * 40
    assert _checked_out_connections(pooled_pg) == 0
    assert _checked_out_connections(pooled_pg, ro=True) == 0


async def test_child_sessions_do_not_deadlock_when_main_pool_exhausted(
    database: DbAccessor,
    make_pooled_pg: "Callable[..., Awaitable[DbAccessor]]",
) -> None:
    # Регрессия: на общем пуле main-сессия держит единственное соединение,
    # ожидая child-ветку, которая ждёт то же соединение из пула — взаимное
    # ожидание до pool_timeout. С выделенным RO-пулом граф ожиданий ацикличен.
    accessor = await make_pooled_pg(
        msgspec.structs.replace(database.config, pool_max_size=1, max_overflow=0, pool_timeout=5.0)
    )

    async def request_scope() -> None:
        async with accessor.new_session():
            await accessor.scalar(_select("1"))  # main занимает rw-соединение
            await asyncio.gather(accessor.scalar(_select("pg_sleep(0.1)::text")))

    await asyncio.wait_for(
        asyncio.gather(request_scope(), request_scope()),
        timeout=GATHER_TIMEOUT_SECONDS,
    )


async def test_straggler_session_closed_when_task_finally_finishes(pooled_pg: DbAccessor) -> None:
    release = asyncio.Event()
    session_taken = asyncio.Event()

    async def stubborn_branch() -> None:
        await pooled_pg.scalar(_select("1"))  # материализует child-сессию
        session_taken.set()
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            await release.wait()  # переживает grace-период close_children
            raise

    async with pooled_pg.new_session():
        task = asyncio.create_task(stubborn_branch())
        await session_taken.wait()  # ветка успела взять сессию

    assert _checked_out_connections(pooled_pg, ro=True) == 1, "страгглер ещё держит сессию"
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    # Сессию страгглера закрывает его done-callback в фоновой cleanup-задаче.
    await wait_until_async(
        lambda: _checked_out_connections(pooled_pg, ro=True) == 0,
        interval_seconds=0.01,
        message="сессия страгглера должна быть закрыта после завершения его задачи",
    )


async def test_uow_from_child_task_raises(database: DbAccessor) -> None:
    uow = PgUnitOfWork(database)

    async def child_uow() -> None:
        async with uow():
            pass

    async with database.new_session():
        scope = database._current_scope.get()  # type: ignore[attr-defined]
        assert scope is not None

        def fail_session_maker() -> None:
            raise AssertionError("гард uow не должен лениво создавать child-сессию")

        scope._ro_session_maker = fail_session_maker
        with pytest.raises(RuntimeError, match="child task"):
            await asyncio.wait_for(
                asyncio.gather(child_uow()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_warns_on_child_session_after_writes(
    database: DbAccessor,
    person_repository: PersonRepository,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="roots_of_rhythm.infrastructure.session_scope"):
        async with database.new_session():
            await person_repository.add(create_person("Sam"))
            await asyncio.wait_for(
                asyncio.gather(database.scalar(_select("1"))),
                timeout=GATHER_TIMEOUT_SECONDS,
            )

    assert any("after main-session writes" in r.message for r in caplog.records), (
        "создание child-сессии после записей основной сессии должно логировать warning"
    )


async def test_nested_new_session_returns_inner_then_outer(database: DbAccessor) -> None:
    async with database.new_session() as outer:
        assert database.get_current_session() is outer
        async with database.new_session() as inner:
            assert inner is not outer
            assert database.get_current_session() is inner
        assert database.get_current_session() is outer
    assert database.get_current_session() is None
