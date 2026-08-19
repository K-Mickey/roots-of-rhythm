from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import (
    ExternalIdentityView,
    GenreSummary,
    PerformerOverviewResponse,
    PersonDateView,
)
from roots_of_rhythm.discovery.application.errors import PerformerOverviewNotFound

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type PeopleUnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]
type MusicUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class PerformerOverviewReader(Protocol):
    async def get(self, performer_id: UUID) -> PerformerOverviewResponse: ...


class PerformerOverviewQuery:
    def __init__(
        self,
        people_uow_factory: PeopleUnitOfWorkFactory,
        music_uow_factory: MusicUnitOfWorkFactory,
    ) -> None:
        self._people_uow_factory = people_uow_factory
        self._music_uow_factory = music_uow_factory

    async def get(self, performer_id: UUID) -> PerformerOverviewResponse:
        async with self._people_uow_factory() as people_uow:
            person = await people_uow.persons.get_published(performer_id)
        if person is None:
            raise PerformerOverviewNotFound(str(performer_id))

        async with self._music_uow_factory() as music_uow:
            assignments = await music_uow.assignments.list_published_for_person(performer_id)
            genres = await music_uow.genres.get_published_by_ids([assignment.concept_id for assignment in assignments])

        summaries = sorted(
            (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres.values()),
            key=lambda item: item.name,
        )
        return PerformerOverviewResponse(
            id=str(person.id),
            name=person.canonical_name,
            aliases=list(person.aliases),
            biography=person.biography,
            birth_date=(
                PersonDateView(
                    year=person.birth_date.year,
                    precision=person.birth_date.precision,
                )
                if person.birth_date is not None
                else None
            ),
            death_date=(
                PersonDateView(
                    year=person.death_date.year,
                    precision=person.death_date.precision,
                )
                if person.death_date is not None
                else None
            ),
            external_identities=[
                ExternalIdentityView(
                    provider=identity.provider,
                    identifier=identity.identifier,
                    url=identity.url,
                )
                for identity in person.external_identities
            ],
            primary_image=None,
            genres=summaries,
        )
