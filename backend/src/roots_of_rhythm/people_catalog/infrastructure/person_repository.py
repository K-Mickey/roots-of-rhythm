from typing import TYPE_CHECKING, Any, Collection

import sqlalchemy as sa

from roots_of_rhythm.infrastructure.repositories.base import PgBaseRepository
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus,
    ExternalIdentity,
    Person,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.application.ports import DbAccessor


class PgPersonRepository(PgBaseRepository[PersonRecord, Person]):
    def __init__(self, database: DbAccessor) -> None:
        super().__init__(database, PersonRecord)

    async def get_published(self, id_: UUID, *, for_update: bool = False) -> Person | None:
        query = sa.select(self.model).where(
            self.model.id == id_,
            self.model.editorial_status == EditorialStatus.PUBLISHED.value,
            self.model.deleted.is_(False),
        )
        if for_update:
            query = query.with_for_update()
        result = await self._db.scalar(query)
        return self.to_domain(result) if result else None

    async def get_published_by_ids(self, ids: Collection[UUID], *, for_update: bool = False) -> dict[UUID, Person]:
        ids = sorted(set(ids))
        if not ids:
            return {}
        query = (
            sa.select(self.model)
            .where(
                self.model.id.in_(ids),
                self.model.editorial_status == EditorialStatus.PUBLISHED.value,
                self.model.deleted.is_(False),
            )
            .order_by(self.model.id)
        )
        if for_update:
            query = query.with_for_update()
        result = await self._db.scalars(query)
        return {record.id: self.to_domain(record) for record in result}

    async def list_published(self) -> tuple[Person, ...]:
        query = (
            sa.select(self.model)
            .where(
                self.model.editorial_status == EditorialStatus.PUBLISHED.value,
                self.model.deleted.is_(False),
            )
            .order_by(self.model.canonical_name)
        )
        result = await self._db.scalars(query)
        return tuple(self.to_domain(record) for record in result)

    def to_dict(self, value: Person, *, pop_id: bool = False) -> dict[str, Any]:
        birth_date = value.birth_date
        death_date = value.death_date
        result = {
            "id": value.id,
            "editorial_status": value.editorial_status.value,
            "canonical_name": value.canonical_name,
            "aliases": list(value.aliases),
            "biography": value.biography,
            "birth_year": birth_date.year if birth_date is not None else None,
            "birth_precision": birth_date.precision.value if birth_date is not None else None,
            "death_year": death_date.year if death_date is not None else None,
            "death_precision": death_date.precision.value if death_date is not None else None,
            "external_identities": [
                {"provider": identity.provider, "identifier": identity.identifier, "url": identity.url}
                for identity in value.external_identities
            ],
        }
        if pop_id:
            result.pop("id", None)
        return result

    def to_domain(self, value: PersonRecord) -> Person:
        return Person.create(
            value.id,
            PersonContent.create(
                value.canonical_name,
                aliases=tuple(value.aliases),
                biography=value.biography,
                birth_date=self._person_date(value.birth_year, value.birth_precision),
                death_date=self._person_date(value.death_year, value.death_precision),
                external_identities=tuple(
                    ExternalIdentity.create(
                        identity["provider"],
                        identity["identifier"],
                        url=identity["url"],
                    )
                    for identity in value.external_identities
                ),
            ),
            editorial_status=EditorialStatus(value.editorial_status),
        )

    @staticmethod
    def _person_date(year: int | None, precision: str | None) -> PersonDate | None:
        if year is None or precision is None:
            return None
        return PersonDate(year=year, precision=TemporalPrecision(precision))
