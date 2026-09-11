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
from roots_of_rhythm.infrastructure.repositories.base import BasePgRepository
from roots_of_rhythm.infrastructure.uow import PgUnitOfWork
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord
from tests.support.waiting import wait_until_async

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from sqlalchemy.sql import Select

    from roots_of_rhythm.infrastructure.base import PgConfig

    # Совместимость переносимых тестов: редкие тесты ссылаются на типы старого
    # app-стека, который в этом репозитории не портирован (решение: оставить их красными).
    PgUserRepository = Any

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

GATHER_TIMEOUT_SECONDS = 15.0


def _select(sql: str) -> "Select[Any]":
    """SQL-выражение (без ключевого слова SELECT) в Select — scalar-хелперы типизированы под TypedReturnsRows."""
    return sa.select(text(sql))


@pytest.fixture
def user_repo(pg: PgAccessor) -> "BasePgRepository[PersonRecord]":
    # TODO(port): user-репозиторий не портирован; два repo-теста намеренно остаются
    # красными (create(keycloak_id=...) не матчит колонки persons).
    return BasePgRepository(pg, PersonRecord)


def _checked_out_connections(accessor: PgAccessor, *, ro: bool = False) -> int:
    pool = (accessor.ro_engine if ro else accessor.engine).pool
    assert isinstance(pool, QueuePool)
    return pool.checkedout()


@pytest_asyncio.fixture(loop_scope="function")
async def make_pooled_pg(pg: PgAccessor) -> "AsyncGenerator[Callable[..., Awaitable[PgAccessor]], None]":
    accessors: list[PgAccessor] = []

    async def factory(config: PgConfig | None = None) -> PgAccessor:
        accessor = PgAccessor(config=config or pg.config)
        await accessor.connect()
        accessors.append(accessor)
        return accessor

    yield factory
    for accessor in accessors:
        await accessor.disconnect()


@pytest_asyncio.fixture(loop_scope="function")
async def pooled_pg(make_pooled_pg: "Callable[..., Awaitable[PgAccessor]]") -> PgAccessor:
    return await make_pooled_pg()


async def test_gather_on_request_session_does_not_share_connection(pg: PgAccessor) -> None:
    async with pg.new_session():
        results = await asyncio.wait_for(
            asyncio.gather(*[pg.scalar(_select("pg_sleep(0.1)::text")) for _ in range(5)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
    assert len(results) == 5


async def test_gather_branches_use_own_connections(pg: PgAccessor) -> None:
    async def branch_pids() -> tuple[int | None, int | None]:
        first: int | None = await pg.scalar(_select("pg_backend_pid()"))
        second: int | None = await pg.scalar(_select("pg_backend_pid()"))
        return first, second

    async with pg.new_session():
        main_pid_before = await pg.scalar(_select("pg_backend_pid()"))
        branches = await asyncio.wait_for(
            asyncio.gather(*[branch_pids() for _ in range(3)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )
        main_pid_after = await pg.scalar(_select("pg_backend_pid()"))

    assert main_pid_before == main_pid_after
    branch_pid_values = {pids[0] for pids in branches}
    for first, second in branches:
        assert first == second, "внутри одной ветки должна использоваться одна сессия"
    assert len(branch_pid_values) == 3, "ветки должны работать в разных соединениях"
    assert main_pid_before not in branch_pid_values, "ветки не должны делить соединение главной задачи"


async def test_child_branch_is_read_only(pg: PgAccessor) -> None:
    async def write_branch() -> None:
        await pg.execute(text("UPDATE persons SET biography = biography"))

    async with pg.new_session():
        with pytest.raises(DBAPIError, match="read-only"):
            await asyncio.wait_for(
                asyncio.gather(write_branch()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_child_does_not_see_uncommitted_main_writes(
    pg: PgAccessor,
    user_repo: PgUserRepository,
) -> None:
    keycloak_id = "scope-uncommitted-visibility"
    count_q = text("select count(*) from users where keycloak_id = :kid")

    async def child_count() -> int | None:
        return await pg.scalar(sa.select(count_q.bindparams(kid=keycloak_id)))

    async with pg.new_session():
        await user_repo.create(
            keycloak_id=keycloak_id,
            email="scope@test.com",
            first_name="Тест",
            last_name="Скоуп",
        )
        (child_visible,) = await asyncio.wait_for(
            asyncio.gather(child_count()),
            timeout=GATHER_TIMEOUT_SECONDS,
        )

    assert child_visible == 0, "ветка не должна видеть незакоммиченные записи главной сессии"
    assert await pg.scalar(sa.select(count_q.bindparams(kid=keycloak_id))) == 1, "после commit запись видна"


async def test_no_connection_leak_after_scope(pooled_pg: PgAccessor) -> None:
    async with pooled_pg.new_session():
        await asyncio.wait_for(
            asyncio.gather(*[pooled_pg.scalar(_select("pg_sleep(0.05)::text")) for _ in range(4)]),
            timeout=GATHER_TIMEOUT_SECONDS,
        )

    assert _checked_out_connections(pooled_pg) == 0
    assert _checked_out_connections(pooled_pg, ro=True) == 0


async def test_cancelled_siblings_do_not_leak(pooled_pg: PgAccessor) -> None:
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


async def test_child_dml_statement_raises(pg: PgAccessor) -> None:
    async def write_branch() -> None:
        await pg.execute(sa.update(PersonRecord).values(biography=PersonRecord.biography))

    async with pg.new_session():
        with pytest.raises(RuntimeError, match="read-only child"):
            await asyncio.wait_for(
                asyncio.gather(write_branch()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_child_session_released_when_task_finishes(pooled_pg: PgAccessor) -> None:
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


async def test_many_child_branches_do_not_exhaust_pool(pooled_pg: PgAccessor) -> None:
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
    pg: PgAccessor,
    make_pooled_pg: "Callable[..., Awaitable[PgAccessor]]",
) -> None:
    # Регрессия: на общем пуле main-сессия держит единственное соединение,
    # ожидая child-ветку, которая ждёт то же соединение из пула — взаимное
    # ожидание до pool_timeout. С выделенным RO-пулом граф ожиданий ацикличен.
    accessor = await make_pooled_pg(
        msgspec.structs.replace(pg.config, pool_max_size=1, max_overflow=0, pool_timeout=5.0)
    )

    async def request_scope() -> None:
        async with accessor.new_session():
            await accessor.scalar(_select("1"))  # main занимает rw-соединение
            await asyncio.gather(accessor.scalar(_select("pg_sleep(0.1)::text")))

    await asyncio.wait_for(
        asyncio.gather(request_scope(), request_scope()),
        timeout=GATHER_TIMEOUT_SECONDS,
    )


async def test_straggler_session_closed_when_task_finally_finishes(pooled_pg: PgAccessor) -> None:
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


async def test_uow_from_child_task_raises(pg: PgAccessor) -> None:
    uow = PgUnitOfWork(pg)

    async def child_uow() -> None:
        async with uow():
            pass

    async with pg.new_session():
        scope = pg._current_scope.get()
        assert scope is not None

        def fail_session_maker() -> None:
            raise AssertionError("гард uow не должен лениво создавать child-сессию")

        scope._ro_session_maker = fail_session_maker  # type: ignore[assignment]
        with pytest.raises(RuntimeError, match="child task"):
            await asyncio.wait_for(
                asyncio.gather(child_uow()),
                timeout=GATHER_TIMEOUT_SECONDS,
            )


async def test_warns_on_child_session_after_writes(
    pg: PgAccessor,
    user_repo: PgUserRepository,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.infrastructure.db.pg_accessor"):
        async with pg.new_session():
            await user_repo.create(
                keycloak_id="scope-warn-after-write",
                email="scope-warn@test.com",
                first_name="Тест",
                last_name="Ворнинг",
            )
            await asyncio.wait_for(
                asyncio.gather(pg.scalar(_select("1"))),
                timeout=GATHER_TIMEOUT_SECONDS,
            )

    assert any("after main-session writes" in r.message for r in caplog.records), (
        "создание child-сессии после записей основной сессии должно логировать warning"
    )


async def test_nested_new_session_returns_inner_then_outer(pg: PgAccessor) -> None:
    async with pg.new_session() as outer:
        assert pg.get_current_session() is outer
        async with pg.new_session() as inner:
            assert inner is not outer
            assert pg.get_current_session() is inner
        assert pg.get_current_session() is outer
    assert pg.get_current_session() is None
