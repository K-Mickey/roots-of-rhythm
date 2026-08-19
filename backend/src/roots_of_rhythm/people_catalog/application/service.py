from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.people_catalog.application.errors import PersonNotFound
from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork
from roots_of_rhythm.people_catalog.domain import Person, PersonContent

type UnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]


class PersonService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(self, content: PersonContent, *, person_id: UUID | None = None) -> Person:
        async with self._uow_factory() as uow:
            person = Person.create(person_id or uuid7(), content)
            await uow.persons.add(person)
            await uow.commit()
            return person

    async def replace_content(self, person_id: UUID, content: PersonContent) -> Person:
        async with self._uow_factory() as uow:
            person = await self._get(uow, person_id)
            updated = person.replace_content(content)
            try:
                await uow.persons.save(updated)
            except LookupError as error:
                raise PersonNotFound(str(person_id)) from error
            await uow.commit()
            return updated

    async def publish(self, person_id: UUID) -> Person:
        return await self._change_status(person_id, Person.publish)

    async def archive(self, person_id: UUID) -> Person:
        return await self._change_status(person_id, Person.archive)

    async def _change_status(self, person_id: UUID, transition: Callable[[Person], Person]) -> Person:
        async with self._uow_factory() as uow:
            person = await self._get(uow, person_id)
            updated = transition(person)
            try:
                await uow.persons.save(updated)
            except LookupError as error:
                raise PersonNotFound(str(person_id)) from error
            await uow.commit()
            return updated

    @staticmethod
    async def _get(uow: PeopleCatalogUnitOfWork, person_id: UUID) -> Person:
        person = await uow.persons.get(person_id)
        if person is None:
            raise PersonNotFound(str(person_id))
        return person
