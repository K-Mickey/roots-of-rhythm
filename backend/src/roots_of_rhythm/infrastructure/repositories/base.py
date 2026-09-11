from typing import TYPE_CHECKING, Any, Callable, Generic, Protocol, TypeVar

import sqlalchemy as sa

from roots_of_rhythm.infrastructure.repositories.mixins import PaginationMixin

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor


class PersistableModel(Protocol):
    """Минимальный контракт модели для ``BasePgRepository``.

    Дополнительные опциональные атрибуты модели (проверяются утиной типизацией):

    - ``from_db_row(row: Mapping[str, Any]) -> Model`` — конструктор из строки БД;
    - ``ignore_columns: Sequence[str]`` — столбцы, исключаемые из INSERT.
    """

    id: Any


ModelT = TypeVar("ModelT", bound=PersistableModel)


class BasePgRepository(PaginationMixin, Generic[ModelT]):
    def __init__(self, pg: "PgAccessor", model: "type[ModelT]") -> None:
        self._pg = pg
        self._model = model
        self._table: sa.Table = model.__table__  # type: ignore[attr-defined]

    @property
    def model(self) -> "type[ModelT]":
        return self._model

    @property
    def table(self) -> sa.Table:
        return self._table

    @staticmethod
    def escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def row_to_model(self, row: "Mapping[str, Any]") -> ModelT:
        from_db_row: "Callable[[Mapping[str, Any]], ModelT] | None" = getattr(self.model, "from_db_row", None)
        if from_db_row is not None:
            return from_db_row(row)
        return self.model(**dict(row))

    async def exists(
        self,
        *clauses: Any,
        session: "AsyncSession | None" = None,
    ) -> bool:
        q = sa.select(self.model.id).where(*clauses).limit(1)
        result = await self._pg.scalar(q, session=session)
        return result is not None

    async def count(
        self,
        *clauses: Any,
        session: "AsyncSession | None" = None,
    ) -> int:
        q = sa.select(sa.func.count()).select_from(self.model).where(*clauses)
        total = await self._pg.scalar(q, session=session)
        return total or 0

    async def get(
        self,
        id_: Any,
        *,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "ModelT | None":
        q = sa.select(self.model).where(self.model.id == id_)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar(q, session=session)

    async def one(
        self,
        *clauses: Any,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> ModelT:
        q = sa.select(self.model).where(*clauses)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar_one(q, session=session)

    async def one_value(
        self,
        column: "sa.Column[Any]",
        *clauses: Any,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> Any:
        q = sa.select(column).where(*clauses)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar_one(q, session=session)

    async def one_or_none(
        self,
        *clauses: Any,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "ModelT | None":
        q = sa.select(self.model).where(*clauses)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar_one_or_none(q, session=session)

    async def one_value_or_none(
        self,
        column: "sa.Column[Any]",
        *clauses: Any,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> Any | None:
        q = sa.select(column).where(*clauses)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar_one_or_none(q, session=session)

    async def first(
        self,
        *clauses: Any,
        order_by: "Sequence[sa.ColumnElement[Any]] | None" = None,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "ModelT | None":
        q = sa.select(self.model).where(*clauses).limit(1)
        if order_by:
            q = q.order_by(*order_by)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar(q, session=session)

    async def first_value(
        self,
        column: "sa.Column[Any]",
        *clauses: Any,
        order_by: "Sequence[sa.ColumnElement[Any]] | None" = None,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> Any | None:
        q = sa.select(column).where(*clauses).limit(1)
        if order_by:
            q = q.order_by(*order_by)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalar(q, session=session)

    async def get_all(
        self,
        *clauses: Any,
        order_by: "Sequence[sa.ColumnElement[Any]] | None" = None,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "Iterable[ModelT]":
        q = sa.select(self.model).where(*clauses)
        if order_by:
            q = q.order_by(*order_by)
        if for_update:
            q = q.with_for_update()
        result = await self._pg.execute(q, session=session)
        scalar_result = result.unique().scalars()
        return scalar_result

    async def get_flat(
        self,
        column: "sa.Column[Any]",
        *clauses: Any,
        order_by: "Sequence[sa.ColumnElement[Any]] | None" = None,
        for_update: bool = False,
        session: "AsyncSession | None" = None,
    ) -> "Iterable[Any]":
        q = sa.select(column).where(*clauses)
        if order_by:
            q = q.order_by(*order_by)
        if for_update:
            q = q.with_for_update()
        return await self._pg.scalars(q, session=session)

    async def create(
        self,
        obj: "ModelT | dict[str, Any]",
        pop_id: bool = True,
        session: "AsyncSession | None" = None,
    ) -> ModelT:
        item = self._obj_to_dict(obj, pop_id=pop_id)
        q = sa.insert(self.model).values(**item).returning(self.table)
        result = await self._pg.first(q, session=session)
        if result is None:
            raise RuntimeError("insert returned no row")
        row = dict(result._mapping)
        return self.row_to_model(row)

    async def update(
        self,
        id_: Any,
        updates: "dict[str, Any]",
        session: "AsyncSession | None" = None,
    ) -> int:
        return await self.update_all(
            self.model.id == id_,
            updates=updates,
            session=session,
        )

    async def update_all(
        self,
        *clauses: Any,
        updates: "dict[str, Any]",
        session: "AsyncSession | None" = None,
    ) -> int:
        if not updates:
            return 0
        q = sa.update(self.model).values(**updates).where(*clauses)
        result = await self._pg.execute(q, session=session)
        return result.rowcount or 0

    async def update_obj(
        self,
        obj: ModelT,
        updates: "dict[str, Any] | None",
        update_obj: bool = True,
        session: "AsyncSession | None" = None,
    ) -> ModelT:
        if not updates:
            return obj

        obj_id = obj.id
        await self.update(obj_id, updates, session=session)

        if update_obj:
            for k, v in updates.items():
                setattr(obj, k, v)

        return obj

    async def delete(self, id_: Any, session: "AsyncSession | None" = None) -> int:
        return await self.delete_all(self.model.id == id_, session=session)

    async def delete_all(
        self,
        *clauses: Any,
        session: "AsyncSession | None" = None,
    ) -> int:
        q = sa.delete(self.model).where(*clauses)
        result = await self._pg.execute(q, session=session)
        return result.rowcount or 0

    def _obj_to_dict(self, obj: "ModelT | dict[str, Any]", pop_id: bool = True) -> "dict[str, Any]":
        if isinstance(obj, dict):
            item = dict(obj)
        else:
            mapper: "sa.orm.Mapper[Any] | None" = sa.inspect(self.model)
            item = {c.key: getattr(obj, c.key) for c in mapper.column_attrs}  # type: ignore[union-attr]

        if pop_id:
            item.pop("id", None)

        for column in getattr(self.model, "ignore_columns", []):
            item.pop(column, None)

        return item
