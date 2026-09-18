from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncGenerator, Protocol, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import Delete, Insert, Result, ScalarResult, Update
    from sqlalchemy.engine import CursorResult, Row
    from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker
    from sqlalchemy.sql.selectable import TypedReturnsRows

    from roots_of_rhythm.infrastructure.base import PgConfig

_T = TypeVar("_T")
_R = TypeVar("_R", bound=tuple[Any, ...])


class DbAccessor(Protocol):
    @property
    def config(self) -> PgConfig: ...

    @property
    def engine(self) -> AsyncEngine: ...

    @property
    def ro_engine(self) -> AsyncEngine: ...

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]: ...

    @property
    def ro_session_maker(self) -> async_sessionmaker[AsyncSession]: ...

    @property
    def is_connected(self) -> bool: ...

    def acquire(self) -> AsyncConnection: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def wait_connected(self) -> None: ...

    def reset_request_scope(self) -> None: ...

    @asynccontextmanager
    def new_session(self) -> AsyncGenerator[AsyncSession, None]: ...

    def get_current_session(self) -> AsyncSession | None: ...

    def in_child_task(self) -> bool: ...

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

    async def scalar(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T | None": ...

    async def scalars(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "ScalarResult[_T]": ...

    async def scalar_one(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T": ...

    async def scalar_one_or_none(
        self,
        statement: "TypedReturnsRows[tuple[_T]]",
        *args: Any,
        **kwargs: Any,
    ) -> "_T | None": ...

    async def one(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R]": ...

    async def one_or_none(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R] | None": ...

    async def first(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Row[_R] | None": ...

    async def all(
        self,
        statement: "TypedReturnsRows[_R]",
        *args: Any,
        **kwargs: Any,
    ) -> "Sequence[Row[_R]]": ...
