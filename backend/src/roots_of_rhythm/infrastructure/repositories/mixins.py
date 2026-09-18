import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import ScalarResult
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import Select
    from sqlalchemy.sql.selectable import TypedReturnsRows

    from roots_of_rhythm.application.ports import DbAccessor

_R = TypeVar("_R", bound=tuple[Any, ...])


class PaginationMixin:
    if TYPE_CHECKING:
        _db: DbAccessor

    async def paginate(
        self,
        query: "Select[Any]",
        limit: int = 10,
        offset: int = 0,
        page: int = 1,
        scalars: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "Sequence[Row[Any]] | ScalarResult[Any]":
        offset = offset + limit * max(0, (page - 1))
        query = query.offset(offset).limit(limit)

        if scalars:
            return await self._db.scalars(query, session=session)
        return await self._db.all(query, session=session)

    async def count_and_page(
        self,
        count_query: "TypedReturnsRows[tuple[int]]",
        rows_query: "TypedReturnsRows[_R]",
        session: "AsyncSession | None" = None,
    ) -> "tuple[int, Sequence[Row[_R]]]":
        if session is not None:
            total_row = await self._db.first(count_query, session=session)
            rows = await self._db.all(rows_query, session=session)
        else:
            total_row, rows = await asyncio.gather(
                self._db.first(count_query),
                self._db.all(rows_query),
            )
        return (total_row[0] if total_row else 0), rows
