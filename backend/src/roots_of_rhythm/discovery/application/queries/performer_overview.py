from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    ExternalIdentityView,
    GenreSummary,
    PersonDateView,
)
from roots_of_rhythm.discovery.application.dto.performers import (
    PerformerOverviewResponse,
)
from roots_of_rhythm.discovery.application.errors.performers import PerformerOverviewNotFound

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.public.performer_reader import PerformerReader
    from roots_of_rhythm.people_catalog.domain import PersonDate
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReader


@runtime_checkable
class PerformerOverviewReader(Protocol):
    async def get(self, performer_id: UUID) -> PerformerOverviewResponse: ...


class PerformerOverviewQuery:
    def __init__(
        self,
        people: PublishedPeopleReader,
        performer: PerformerReader,
    ) -> None:
        self._people = people
        self._performer = performer

    async def get(self, performer_id: UUID) -> PerformerOverviewResponse:
        person = await self._people.get_published(performer_id)
        if person is None:
            raise PerformerOverviewNotFound(str(performer_id))

        genres = (await self._performer.get_performer_data(performer_id)).genres
        summaries = sorted(
            (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres.values()),
            key=lambda item: item.name,
        )
        return PerformerOverviewResponse(
            id=str(person.id),
            name=person.canonical_name,
            aliases=list(person.aliases),
            biography=person.biography,
            birth_date=_map_person_date(person.birth_date),
            death_date=_map_person_date(person.death_date),
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


def _map_person_date(date_: PersonDate | None) -> PersonDateView | None:
    if date_ is None:
        return None
    return PersonDateView(
        year=date_.year,
        precision=date_.precision,
    )
