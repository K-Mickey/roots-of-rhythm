from __future__ import annotations

import logging
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import event, literal
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from roots_of_rhythm.config import PGSettings
from roots_of_rhythm.infrastructure.base import PgConfig, build_session_makers
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from tests.support.session import _FakeSession

if TYPE_CHECKING:
    from collections.abc import Iterator

    from roots_of_rhythm.application.ports import DbAccessor

logger = logging.getLogger(__name__)


@contextmanager
def collect_select_statements() -> Iterator[list[str]]:
    statements: list[str] = []

    def _collect_statement(_conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _collect_statement)
    try:
        yield statements
    finally:
        event.remove(Engine, "before_cursor_execute", _collect_statement)


def run_migrations(database_url: str) -> None:
    backend_root = Path(__file__).resolve().parents[2]  #  -> backend/
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")


def create_test_pg_settings() -> PGSettings:
    raw = environ["TEST_DATABASE_URL"]
    url = make_url(raw)
    return PGSettings(
        database=url.database or "",
        host=url.host or "127.0.0.1",
        port=url.port or 5432,
        username=url.username,
        password=url.password,
    )


def create_test_pg_config() -> PgConfig:
    url = create_test_pg_settings()
    return PgConfig(
        database=url.database or "",
        host=url.host or "127.0.0.1",
        port=url.port or 5432,
        username=url.username,
        password=url.password,
    )


async def close_leaked_pg_request_scope(db: DbAccessor) -> None:
    """Close a request scope leaked across tests under session-scoped asyncio loop.

    Production ``reset_request_scope()`` only clears the ContextVar and leaves the
    connection checked out (idle in transaction), which then blocks TRUNCATE/DROP.
    This test helper rolls back/closes the orphaned session so the pool can reuse it.
    """
    scope = db._current_scope.get()  # type: ignore[attr-defined]
    if scope is None:
        return

    db.reset_request_scope()
    scope._closed = True

    try:
        await scope._main_session.rollback()
    except Exception:
        logger.exception("failed to rollback leaked test pg session")

    try:
        await scope._main_session.close()
    except Exception:
        logger.exception("failed to close leaked test pg session")

    await scope.close_children()


async def connect_test_db(db: DbAccessor) -> None:
    url = URL.create(
        drivername="postgresql+asyncpg",
        host=db.config.host,
        port=db.config.port,
        username=db.config.username,
        password=db.config.password,
        database=db.config.database,
    )

    db._engine = create_async_engine(url, poolclass=NullPool)  # type: ignore[attr-defined]
    db._ro_engine = db._engine  # type: ignore[attr-defined]
    db._session_maker, db._ro_session_maker = build_session_makers(db._engine, db._ro_engine, db.config)  # type: ignore[attr-defined]

    await db.scalar(sa.select(literal(1)))


def create_stub_accessor() -> DbAccessor:
    db = PgAccessor(PgConfig(database="stub"))
    db._session_maker = _FakeSession  # type: ignore[assignment]  # noqa: SLF001
    db._ro_session_maker = _FakeSession  # type: ignore[assignment]  # noqa: SLF001
    return db
