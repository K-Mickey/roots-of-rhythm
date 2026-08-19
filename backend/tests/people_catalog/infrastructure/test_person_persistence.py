from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import (
    ExternalIdentity,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_person_repository_round_trips_content_allows_duplicate_names_and_soft_deletes(
    engine: AsyncEngine,
) -> None:
    session_factory = create_session_factory(engine)
    service = PersonService(lambda: SqlAlchemyPeopleCatalogUnitOfWork(session_factory))
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
    first = await service.create(content)
    duplicate = await service.create(PersonContent.create("John Smith"))
    await service.publish(first.id)
    await service.publish(duplicate.id)
    archived = await service.create(PersonContent.create("Archived"))
    await service.publish(archived.id)
    await service.archive(archived.id)
    draft = await service.create(PersonContent.create("Draft"))

    async with SqlAlchemyPeopleCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.persons.get_published(first.id)
        listed = await uow.persons.list_published()

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

    async with SqlAlchemyPeopleCatalogUnitOfWork(session_factory) as uow:
        await uow.persons.mark_deleted(first.id)
        await uow.commit()
    async with SqlAlchemyPeopleCatalogUnitOfWork(session_factory) as uow:
        assert await uow.persons.get(first.id) is None
        assert await uow.persons.get_published(first.id) is None
