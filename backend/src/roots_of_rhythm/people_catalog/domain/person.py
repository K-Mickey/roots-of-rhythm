from uuid import UUID

import msgspec

from roots_of_rhythm.people_catalog.domain.enums import EditorialStatus
from roots_of_rhythm.people_catalog.domain.errors import PersonPublicationError
from roots_of_rhythm.people_catalog.domain.value_objects import ExternalIdentity, PersonContent, PersonDate


class Person(msgspec.Struct, frozen=True):
    id: UUID
    canonical_name: str
    aliases: tuple[str, ...] = ()
    biography: str | None = None
    birth_date: PersonDate | None = None
    death_date: PersonDate | None = None
    external_identities: tuple[ExternalIdentity, ...] = ()
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        person_id: UUID,
        content: PersonContent,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "Person":
        return cls(
            id=person_id,
            canonical_name=content.canonical_name,
            aliases=content.aliases,
            biography=content.biography,
            birth_date=content.birth_date,
            death_date=content.death_date,
            external_identities=content.external_identities,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: PersonContent) -> "Person":
        return Person.create(self.id, content, editorial_status=self.editorial_status)

    def submit_for_review(self) -> "Person":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "Person":
        if not self.canonical_name:
            raise PersonPublicationError(("canonical_name",))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "Person":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "Person":
        return Person(
            id=self.id,
            canonical_name=self.canonical_name,
            aliases=self.aliases,
            biography=self.biography,
            birth_date=self.birth_date,
            death_date=self.death_date,
            external_identities=self.external_identities,
            editorial_status=status,
        )
