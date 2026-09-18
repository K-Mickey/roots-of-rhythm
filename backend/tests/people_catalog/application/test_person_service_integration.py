from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.people_catalog.domain import (
    ExternalIdentity,
    PersonAlreadyExistsError,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)

if TYPE_CHECKING:
    from roots_of_rhythm.people_catalog.domain import Person
    from roots_of_rhythm.people_catalog.public import PeopleCatalog

pytestmark = pytest.mark.integration


async def create_persons(service: PeopleCatalog) -> list[Person]:
    persons = []
    for name in ("Sam", "Kris", "Aaron", "Kenny"):
        person = await service.create(PersonContent(name))
        persons.append(person)

    await service.publish(persons[0].id)
    await service.publish(persons[1].id)
    await service._person_repository.mark_deleted(persons[-1].id)  # type: ignore[attr-defined]
    return persons


async def test_person_service_round_trips_content_allows_duplicate_names(person_service: PeopleCatalog) -> None:
    content = PersonContent.create(
        "John Smith",
        aliases=("Johnny",),
        biography="A performer.",
        birth_date=PersonDate(1900, TemporalPrecision.CIRCA_YEAR),
        death_date=PersonDate(1970, TemporalPrecision.EXACT_YEAR),
        external_identities=(
            ExternalIdentity.create("MusicBrainz", "artist-1", url="https://musicbrainz.org/artist/artist-1"),
        ),
    )
    first = await person_service.create(content)
    duplicate = await person_service.create(PersonContent.create("John Smith"))
    await person_service.publish(first.id)
    await person_service.publish(duplicate.id)
    archived = await person_service.create(PersonContent.create("Archived"))
    await person_service.publish(archived.id)
    await person_service.archive(archived.id)
    draft = await person_service.create(PersonContent.create("Draft"))

    loaded = await person_service._person_repository.get_published(first.id)  # type: ignore[attr-defined]
    listed = await person_service._person_repository.list_published()  # type: ignore[attr-defined]

    assert loaded is not None
    assert loaded.canonical_name == content.canonical_name
    assert loaded.aliases == content.aliases
    assert loaded.biography == content.biography
    assert loaded.birth_date == content.birth_date
    assert loaded.death_date == content.death_date
    assert loaded.external_identities == content.external_identities
    assert {person.id for person in listed} == {first.id, duplicate.id}
    assert [person.canonical_name for person in listed] == ["John Smith", "John Smith"]
    assert draft.id not in {person.id for person in listed}
    assert archived.id not in {person.id for person in listed}


async def test_person_service_create_persons(person_service: PeopleCatalog) -> None:
    content = PersonContent.create("John")
    assert await person_service.create(content) is not None
    assert await person_service.create(content) is not None


async def test_person_service_create_person_already_exists(person_service: PeopleCatalog) -> None:
    content = PersonContent.create("John")
    person_uuid = uuid7()
    await person_service.create(content, person_id=person_uuid)
    with pytest.raises(PersonAlreadyExistsError):
        await person_service.create(content, person_id=person_uuid)


async def test_person_service_replace_content(person_service: PeopleCatalog) -> None:
    person = await person_service.create(PersonContent.create("John Smith"))
    new_content = PersonContent.create("John Smith", biography="A singer")
    await person_service.replace_content(person.id, new_content)
    created = await person_service._person_repository.get(person.id)  # type: ignore[attr-defined]
    assert created
    assert created.id == person.id
    assert created.biography == "A singer"


async def test_person_service_list_published(person_service: PeopleCatalog) -> None:
    await create_persons(person_service)
    published = await person_service.list_published()
    assert len(published) == 2


async def test_person_service_list_published_empty(person_service: PeopleCatalog) -> None:
    published = await person_service.list_published()
    assert len(published) == 0


async def test_person_service_get_published_by_ids(person_service: PeopleCatalog) -> None:
    persons = await create_persons(person_service)
    first, second, third, fourth = persons
    published = await person_service.get_published_by_ids([first.id, second.id, first.id, third.id, fourth.id])
    assert len(published) == 2
    not_published = await person_service.get_published_by_ids([third.id, fourth.id])
    assert len(not_published) == 0


async def test_person_service_get_published_by_ids_empty(person_service: PeopleCatalog) -> None:
    published = await person_service.get_published_by_ids([])
    assert len(published) == 0


async def test_person_service_get_published(person_service: PeopleCatalog) -> None:
    persons = await create_persons(person_service)
    published = await person_service.get_published(persons[0].id)
    assert published is not None and published.canonical_name == "Sam"

    drafted = await person_service.get_published(persons[2].id)
    assert drafted is None
    assert await person_service._person_repository.get(persons[2].id) is not None  # type: ignore[attr-defined]

    deleted = await person_service.get_published(persons[-1].id)
    assert deleted is None
    assert await person_service._person_repository.get(persons[-1].id) is None  # type: ignore[attr-defined]

    assert await person_service.get_published(uuid7()) is None
