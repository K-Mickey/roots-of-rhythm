from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus
from roots_of_rhythm.music_catalog.domain.value_objects import ExistencePeriod, GroupMembershipContent


class GroupMembership(msgspec.Struct, frozen=True):
    id: UUID
    person_id: UUID
    group_id: UUID
    period: ExistencePeriod | None = None
    roles_or_instruments: tuple[str, ...] = ()
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        membership_id: UUID,
        person_id: UUID,
        group_id: UUID,
        content: GroupMembershipContent | None = None,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "GroupMembership":
        normalized = content or GroupMembershipContent.create()
        return cls(
            id=membership_id,
            person_id=person_id,
            group_id=group_id,
            period=normalized.period,
            roles_or_instruments=normalized.roles_or_instruments,
            provenance=normalized.provenance,
            editorial_status=editorial_status,
        )

    @property
    def is_published(self) -> bool:
        return self.editorial_status is EditorialStatus.PUBLISHED

    def replace_content(self, content: GroupMembershipContent) -> "GroupMembership":
        return GroupMembership(
            id=self.id,
            person_id=self.person_id,
            group_id=self.group_id,
            period=content.period,
            roles_or_instruments=content.roles_or_instruments,
            provenance=content.provenance,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "GroupMembership":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "GroupMembership":
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "GroupMembership":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "GroupMembership":
        return GroupMembership(
            id=self.id,
            person_id=self.person_id,
            group_id=self.group_id,
            period=self.period,
            roles_or_instruments=self.roles_or_instruments,
            provenance=self.provenance,
            editorial_status=status,
        )
