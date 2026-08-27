from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    Group,
    GroupContent,
    GroupMembership,
    GroupMembershipContent,
)
from roots_of_rhythm.music_catalog.infrastructure.mapping._temporal import (
    apply_existence_period_columns,
    existence_period_from_columns,
)
from roots_of_rhythm.music_catalog.infrastructure.models import GroupMembershipRecord, GroupRecord


def record_from_group(group: Group) -> GroupRecord:
    record = GroupRecord(
        id=group.id,
        editorial_status=group.editorial_status.value,
        canonical_name=group.canonical_name,
        aliases=list(group.aliases),
        description=group.description,
    )
    apply_existence_period_columns(record, group.period)
    return record


def group_from_record(record: GroupRecord) -> Group:
    return Group.create(
        record.id,
        GroupContent.create(
            record.canonical_name,
            aliases=tuple(record.aliases),
            description=record.description,
            period=existence_period_from_columns(
                record.period_start_year,
                record.period_start_precision,
                record.period_end_year,
                record.period_end_precision,
            ),
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_group_record(record: GroupRecord, group: Group) -> None:
    record.editorial_status = group.editorial_status.value
    record.canonical_name = group.canonical_name
    record.aliases = list(group.aliases)
    record.description = group.description
    apply_existence_period_columns(record, group.period)


def record_from_group_membership(membership: GroupMembership) -> GroupMembershipRecord:
    record = GroupMembershipRecord(
        id=membership.id,
        person_id=membership.person_id,
        group_id=membership.group_id,
        editorial_status=membership.editorial_status.value,
        roles_or_instruments=list(membership.roles_or_instruments),
        provenance=membership.provenance,
    )
    apply_existence_period_columns(record, membership.period)
    return record


def group_membership_from_record(record: GroupMembershipRecord) -> GroupMembership:
    return GroupMembership.create(
        record.id,
        record.person_id,
        record.group_id,
        GroupMembershipContent.create(
            period=existence_period_from_columns(
                record.period_start_year,
                record.period_start_precision,
                record.period_end_year,
                record.period_end_precision,
            ),
            roles_or_instruments=tuple(record.roles_or_instruments),
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_group_membership_record(record: GroupMembershipRecord, membership: GroupMembership) -> None:
    record.editorial_status = membership.editorial_status.value
    record.roles_or_instruments = list(membership.roles_or_instruments)
    record.provenance = membership.provenance
    apply_existence_period_columns(record, membership.period)
