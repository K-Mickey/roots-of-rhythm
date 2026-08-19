from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

_T = TypeVar("_T", bound=tuple[Any, ...])


def create_database_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def apply_write_lock(statement: Select[_T], *, for_update: bool) -> Select[_T]:
    return statement.with_for_update() if for_update else statement


async def check_database_readiness(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
