import asyncio
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, TypeVar, overload

from sqlalchemy import text
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from roots_of_rhythm.infrastructure.base import build_session_makers
from roots_of_rhythm.infrastructure.session_scope import SessionScope

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping, Sequence

    from sqlalchemy import Delete, Insert, Result, ScalarResult, Update
    from sqlalchemy.engine import CursorResult, Row
    from sqlalchemy.ext.asyncio import AsyncConnection
    from sqlalchemy.sql.selectable import TypedReturnsRows

    from roots_of_rhythm.infrastructure.base import PgConfig

_T = TypeVar("_T")
_R = TypeVar("_R", bound=tuple[Any, ...])

logger = logging.getLogger(__name__)


class PgAccessor:
    def __init__(
        self,
        config: PgConfig,
        *,
        create_engine_kwargs: "Mapping[str, Any] | None" = None,
    ) -> None:
        self._config = config
        self._create_engine_kwargs = dict(create_engine_kwargs) if create_engine_kwargs is not None else {}
        self._create_engine_kwargs.setdefault("pool_timeout", config.pool_timeout)
        self._create_engine_kwargs.setdefault("pool_use_lifo", config.pool_use_lifo)
        self._engine: AsyncEngine | None = None
        self._ro_engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None
        self._ro_session_maker: async_sessionmaker[AsyncSession] | None = None
        self._current_scope: ContextVar[SessionScope | None] = ContextVar("current_session_scope", default=None)

        self._connect_lock = asyncio.Lock()
        self._disconnect_lock = asyncio.Lock()
        self._connected_event = asyncio.Event()
        self._is_connected = False

    @property
    def config(self) -> PgConfig:
        return self._config

    @property
    def engine(self) -> AsyncEngine:
        if not self._engine:
            raise ValueError(f"Database `{self.config.database}` is not connected")
        return self._engine

    @property
    def ro_engine(self) -> AsyncEngine:
        if not self._ro_engine:
            raise ValueError(f"Database `{self.config.database}` is not connected (ro engine)")
        return self._ro_engine

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            raise ValueError("Session maker is not initialized")
        return self._session_maker

    @property
    def ro_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._ro_session_maker is None:
            raise ValueError("Read-only session maker is not initialized")
        return self._ro_session_maker

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def acquire(self) -> AsyncConnection:
        return self.engine.connect()

    async def connect(self) -> None:
        async with self._connect_lock:
            if self._is_connected:
                return
            while True:
                try:
                    await self._connect()
                    self._is_connected = True
                    self._connected_event.set()
                    return
                except (OSError, ConnectionRefusedError, OperationalError) as error:
                    logger.warning(
                        "pg connect to %s:%s/%s failed: %s; retry in %ss",
                        self.config.host,
                        self.config.port,
                        self.config.database,
                        error,
                        self.config.reconnect_timeout,
                    )
                    await asyncio.sleep(self.config.reconnect_timeout)

    async def disconnect(self) -> None:
        async with self._disconnect_lock:
            if not self._is_connected:
                return
            await self._disconnect()
            self._is_connected = False
            self._connected_event.clear()

    async def wait_connected(self) -> None:
        await self._connected_event.wait()

    async def _pre_open(self, engine: AsyncEngine) -> None:
        conns: list[AsyncConnection] = []
        err: Exception | None = None
        try:
            for _ in range(self.config.pool_min_size):
                conn = engine.connect()
                conns.append(conn)
                await conn.start()
        finally:
            for conn in conns:
                try:
                    await conn.close()
                except Exception as exc:  # noqa: BLE001
                    err = err or exc
        if err is not None:
            raise err

    def _create_engine(self, *, pool_size: int, max_overflow: int) -> AsyncEngine:
        return create_async_engine(
            URL.create(
                drivername="postgresql+asyncpg",
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                database=self.config.database,
            ),
            connect_args={"server_settings": {"client_encoding": "UTF8"}},
            pool_size=pool_size,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,
            max_overflow=max_overflow,
            query_cache_size=self.config.query_cache_size,
            **self._create_engine_kwargs,
        )

    async def _connect(self) -> None:
        engine = self._create_engine(
            pool_size=self.config.pool_max_size,
            max_overflow=self.config.max_overflow,
        )
        ro_engine = self._create_engine(
            pool_size=self.config.ro_pool_max_size,
            max_overflow=self.config.ro_max_overflow,
        )
        try:
            session_maker, ro_session_maker = build_session_makers(engine, ro_engine, self.config)
            if self.config.pool_min_size > 0:
                await self._pre_open(engine)
            async with engine.connect() as connection:
                await connection.execute(text("select 1"))
        except BaseException:
            try:
                await engine.dispose()
            finally:
                await ro_engine.dispose()
            raise
        self._engine = engine
        self._ro_engine = ro_engine
        self._session_maker = session_maker
        self._ro_session_maker = ro_session_maker

    async def _disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
        if self._ro_engine is not None:
            await self._ro_engine.dispose()
            self._ro_engine = None
        self._session_maker = None
        self._ro_session_maker = None

    def reset_request_scope(self) -> None:
        """Сбросить чужой scope на границе запроса: uvicorn при HTTP/1.1 pipelining
        создаёт таску следующего запроса из контекста предыдущего, пока его
        new_session ещё активен."""
        scope = self._current_scope.get()
        if scope is not None:
            logger.warning("pg session scope leaked into a new request context; resetting")
            self._current_scope.set(None)

    @asynccontextmanager
    async def new_session(self) -> "AsyncGenerator[AsyncSession, None]":
        parent_scope = self._current_scope.get()
        if parent_scope is not None and parent_scope.is_child_task():
            raise RuntimeError(
                "new_session() called from a child task of an active request scope: open "
                "sessions/transactions only in the main task (child tasks get a read-only "
                "session automatically)"
            )
        session: AsyncSession = self.session_maker()
        scope = SessionScope(
            main_task=asyncio.current_task(),
            main_session=session,
            ro_session_maker=self.ro_session_maker,
            warn_threshold=_child_sessions_warn_threshold(self.config),
        )
        token = self._current_scope.set(scope)
        try:
            async with session:
                yield session
                await session.commit()
        finally:
            self._current_scope.reset(token)
            await scope.close_children()

    def get_current_session(self) -> AsyncSession | None:
        scope = self._current_scope.get()
        return scope.peek() if scope is not None else None

    def in_child_task(self) -> bool:
        scope = self._current_scope.get()
        return scope is not None and scope.is_child_task()

    @overload
    async def execute(
        self,
        statement: "Insert | Update | Delete",
        *args: Any,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> "CursorResult[Any]": ...

    @overload
    async def execute(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> "Result[_R]": ...

    @overload
    async def execute(
        self,
        statement: Any,
        *args: Any,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> "Result[Any]": ...

    async def execute(
        self,
        statement: Any,
        *args: Any,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> Any:
        scope = self._current_scope.get()
        if session is not None and scope is not None:
            scope.reject_cross_task_session(session)
        current = session or (scope.get() if scope is not None else None)
        if current is not None:
            if scope is not None and getattr(statement, "is_dml", False):
                scope.on_dml(current)
            result = await current.execute(statement, *args, **kwargs)
            if self.config.autocommit:
                await current.commit()
            return result

        async with self.new_session() as current_session:
            return await current_session.execute(statement, *args, **kwargs)

    async def scalar(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T | None":
        result: "Result[tuple[_T]]" = await self.execute(statement, *args, **kwargs)
        return result.scalar()

    async def scalars(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "ScalarResult[_T]":
        result: "Result[tuple[_T]]" = await self.execute(statement, *args, **kwargs)
        return result.scalars()

    async def scalar_one(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T":
        result: "Result[tuple[_T]]" = await self.execute(statement, *args, **kwargs)
        return result.scalar_one()

    async def scalar_one_or_none(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T | None":
        result: "Result[tuple[_T]]" = await self.execute(statement, *args, **kwargs)
        return result.scalar_one_or_none()

    async def one(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R]":
        result: "Result[_R]" = await self.execute(statement, *args, **kwargs)
        return result.one()

    async def one_or_none(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R] | None":
        result: "Result[_R]" = await self.execute(statement, *args, **kwargs)
        return result.one_or_none()

    async def first(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R] | None":
        result: "Result[_R]" = await self.execute(statement, *args, **kwargs)
        return result.first()

    async def all(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Sequence[Row[_R]]":
        result: "Result[_R]" = await self.execute(statement, *args, **kwargs)
        return result.all()


def _child_sessions_warn_threshold(config: PgConfig) -> int:
    return max(1, (config.ro_pool_max_size + config.ro_max_overflow) // 2)
