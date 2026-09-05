from uuid import uuid7

import pytest
from tests.people_catalog.fakes import FakePersonRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.people_catalog.application.read_services.persons import PersonsReadService
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent


def _person(name: str, status: EditorialStatus = EditorialStatus.PUBLISHED) -> Person:
    return Person.create(uuid7(), PersonContent.create(name), editorial_status=status)


@pytest.mark.asyncio
async def test_persons_read_service_get_published_by_ids_filters_and_empty() -> None:
    louis = _person("Louis Armstrong")
    draft = _person("Hidden", EditorialStatus.DRAFT)
    repo = FakePersonRepository({louis.id: louis, draft.id: draft})
    service = PersonsReadService(fake_transaction_scope(), lambda _t: repo)

    result = await service.get_published_by_ids({louis.id, draft.id})

    assert {item.id for item in result.persons} == {louis.id}
    assert (await service.get_published_by_ids(set())).persons == ()


@pytest.mark.asyncio
async def test_persons_read_service_get_published_hides_unpublished() -> None:
    louis = _person("Louis Armstrong")
    draft = _person("Hidden", EditorialStatus.DRAFT)
    repo = FakePersonRepository({louis.id: louis, draft.id: draft})
    service = PersonsReadService(fake_transaction_scope(), lambda _t: repo)

    assert (await service.get_published(louis.id)) is louis
    assert await service.get_published(draft.id) is None
    assert await service.get_published(uuid7()) is None


@pytest.mark.asyncio
async def test_persons_read_service_list_published_in_order() -> None:
    louis = _person("Louis Armstrong")
    charlie = _person("Charlie Parker")
    draft = _person("Draft", EditorialStatus.DRAFT)
    repo = FakePersonRepository({louis.id: louis, charlie.id: charlie, draft.id: draft})
    service = PersonsReadService(fake_transaction_scope(), lambda _t: repo)

    result = await service.list_published()

    assert [item.canonical_name for item in result] == ["Charlie Parker", "Louis Armstrong"]
