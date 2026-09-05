from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.people_catalog.application.ports import PersonRepository
from roots_of_rhythm.people_catalog.public.published_person_reader import (
    PublishedPeopleReadData,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.people_catalog.domain import Person

type PersonRepositoryFactory = Callable[[Transaction], PersonRepository]


class PersonsReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        person_repository_factory: PersonRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._person_repository_factory = person_repository_factory

    async def get_published_by_ids(self, person_ids: Collection[UUID]) -> PublishedPeopleReadData:
        if not person_ids:
            return PublishedPeopleReadData(())
        ids = set(person_ids)
        async with self._transaction_scope() as transaction:
            persons = await self._person_repository_factory(transaction).get_published_by_ids(ids)
        return PublishedPeopleReadData(tuple(persons.values()))

    async def get_published(self, person_id: UUID) -> Person | None:
        async with self._transaction_scope() as transaction:
            return await self._person_repository_factory(transaction).get_published(person_id)

    async def list_published(self) -> tuple[Person, ...]:
        async with self._transaction_scope() as transaction:
            persons = await self._person_repository_factory(transaction).list_published()
        return tuple(persons)
