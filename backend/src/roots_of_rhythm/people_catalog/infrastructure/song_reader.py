from collections.abc import Callable, Collection
from typing import TYPE_CHECKING

from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData

if TYPE_CHECKING:
    from uuid import UUID

type PeopleUnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]


class SqlAlchemyPublishedPeopleReader:
    def __init__(self, uow_factory: PeopleUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_published_by_ids(self, person_ids: Collection[UUID]) -> PublishedPeopleReadData:
        if not person_ids:
            return PublishedPeopleReadData(())
        async with self._uow_factory() as uow:
            persons = await uow.persons.get_published_by_ids(person_ids)
        return PublishedPeopleReadData(tuple(persons.values()))
