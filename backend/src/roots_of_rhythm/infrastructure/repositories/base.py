from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, cast

import msgspec
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.application.errors import UniqueConstraintViolation
from roots_of_rhythm.infrastructure.repositories.mixins import PaginationMixin
from roots_of_rhythm.utils.sql import is_unique_violation

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.application.ports import DbAccessor


class PersistableModel(Protocol):
    id: Any
    deleted: Any


class PersistableDomain(Protocol):
    @property
    def id(self) -> Any: ...


ModelT = TypeVar("ModelT", bound=PersistableModel)
DomainT = TypeVar("DomainT", bound=PersistableDomain)


class PgBaseRepository(PaginationMixin, Generic[ModelT, DomainT]):
    def __init__(self, database: DbAccessor, model: type[ModelT]) -> None:
        self._db = database
        self._model = model

    @property
    def model(self) -> type[ModelT]:
        return self._model

    def to_domain(self, value: ModelT) -> DomainT:
        raise NotImplementedError

    def to_dict(self, value: DomainT, *, pop_id: bool = False) -> dict[str, Any]:
        result = msgspec.structs.asdict(cast("msgspec.Struct", value))
        if pop_id:
            result.pop("id", None)
        return result

    async def add(self, value: DomainT) -> DomainT:
        query = sa.insert(self.model).values(**self.to_dict(value)).returning(self.model)
        try:
            result = await self._db.scalar_one_or_none(query)
        except IntegrityError as exc:
            if constraint := self._match_unique_constraint(exc):
                raise UniqueConstraintViolation(constraint) from exc
            raise

        if result is None:
            raise RuntimeError("insert returned no row")
        return self.to_domain(result)

    async def get(self, id_: UUID, *, for_update: bool = False) -> DomainT | None:
        query = sa.select(self.model).where(self.model.id == id_, self.model.deleted.is_(False))
        if for_update:
            query = query.with_for_update()
        result = await self._db.scalar(query)
        return self.to_domain(result) if result else None

    async def save(self, value: DomainT) -> DomainT:
        updated = self.to_dict(value, pop_id=True)
        query = (
            sa.update(self.model)
            .where(self.model.id == value.id, self.model.deleted.is_(False))
            .values(**updated)
            .returning(self.model)
        )
        try:
            result = await self._db.scalar_one_or_none(query)
        except IntegrityError as exc:
            if constraint := self._match_unique_constraint(exc):
                raise UniqueConstraintViolation(constraint) from exc
            raise

        if result is None:
            raise LookupError(str(value.id))
        return self.to_domain(result)

    async def mark_deleted(self, id_: UUID) -> None:
        query = sa.update(self.model).where(self.model.id == id_).values(deleted=True)
        await self._db.execute(query)

    def _match_unique_constraint(self, exc: IntegrityError) -> str | None:
        unique_constraints: tuple[str, ...] = getattr(self.model, "__unique_constraints__", ())
        for constraint in unique_constraints:
            if is_unique_violation(exc, constraint):
                return constraint
        return None
