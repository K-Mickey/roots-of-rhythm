from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus
from roots_of_rhythm.music_catalog.domain.errors import GroupPublicationError
from roots_of_rhythm.music_catalog.domain.value_objects import ExistencePeriod, GroupContent


class Group(msgspec.Struct, frozen=True):
    id: UUID
    canonical_name: str
    aliases: tuple[str, ...] = ()
    description: str | None = None
    period: ExistencePeriod | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        group_id: UUID,
        content: GroupContent,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "Group":
        return cls(
            id=group_id,
            canonical_name=content.canonical_name,
            aliases=content.aliases,
            description=content.description,
            period=content.period,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: GroupContent) -> "Group":
        return Group.create(self.id, content, editorial_status=self.editorial_status)

    def submit_for_review(self) -> "Group":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "Group":
        if not self.canonical_name:
            raise GroupPublicationError(("canonical_name",))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "Group":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "Group":
        return Group(
            id=self.id,
            canonical_name=self.canonical_name,
            aliases=self.aliases,
            description=self.description,
            period=self.period,
            editorial_status=status,
        )
