from typing import TYPE_CHECKING

from roots_of_rhythm.discovery.application.dto.common import (
    GroupSummary,
    PerformerSummary,
)
from roots_of_rhythm.discovery.application.dto.recordings import (
    RecordingPrimaryCreditView,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Group, Recording
    from roots_of_rhythm.people_catalog.domain import Person


def project_primary_credits(
    recording: Recording,
    persons: dict[UUID, Person],
    groups: dict[UUID, Group],
) -> list[RecordingPrimaryCreditView]:
    projected: list[RecordingPrimaryCreditView] = []
    for credit in recording.credits:
        if not credit.is_primary_billing:
            continue
        target = persons.get(credit.target_id) if credit.is_person_target else groups.get(credit.target_id)
        if target is None:
            continue
        summary = (
            PerformerSummary(str(target.id), target.canonical_name)
            if credit.is_person_target
            else GroupSummary(str(target.id), target.canonical_name)
        )
        projected.append(RecordingPrimaryCreditView(credit.target_kind, summary))
    return projected
