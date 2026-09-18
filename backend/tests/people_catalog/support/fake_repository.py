from typing import TYPE_CHECKING, cast

from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any
    from uuid import UUID

    from roots_of_rhythm.application.ports import DbAccessor
    from roots_of_rhythm.people_catalog.domain import Person


class FakePersonRepository:
    def __init__(self, persons: dict[UUID, Person]) -> None:
        self._persons = persons
        self.locked_ids: list[UUID] = []
        self.batch_calls: list[tuple[UUID, ...]] = []
        self._db: DbAccessor = cast("DbAccessor", None)
        self._model: type[PersonRecord] = PersonRecord

    @property
    def model(self) -> type[PersonRecord]:
        return self._model

    def to_domain(self, value: PersonRecord) -> Person:
        raise NotImplementedError("fake не конвертирует ORM")

    def to_dict(self, value: Person, *, pop_id: bool = False) -> dict[str, Any]:
        raise NotImplementedError("fake не конвертирует в ORM")

    async def add(self, value: Person) -> Person:
        self._persons[value.id] = value
        return value

    async def get(self, id_: UUID, *, for_update: bool = False) -> Person | None:
        return self._persons.get(id_)

    async def get_published(self, id_: UUID, *, for_update: bool = False) -> Person | None:
        person = self._persons.get(id_)
        return person if person is not None and person.is_published else None

    async def get_published_by_ids(self, ids: Collection[UUID], *, for_update: bool = False) -> dict[UUID, Person]:
        ids = sorted(set(ids))
        self.batch_calls.append(tuple(ids))
        if for_update:
            self.locked_ids.extend(ids)
        return {
            person_id: person
            for person_id in ids
            if (person := self._persons.get(person_id)) is not None and person.is_published
        }

    async def list_published(self) -> tuple[Person, ...]:
        return tuple(
            sorted(
                (person for person in self._persons.values() if person.is_published),
                key=lambda person: person.canonical_name,
            )
        )

    async def save(self, value: Person) -> Person:
        if value.id not in self._persons:
            raise LookupError(str(value.id))
        self._persons[value.id] = value
        return value

    async def mark_deleted(self, id_: UUID) -> None:
        self._persons.pop(id_, None)
