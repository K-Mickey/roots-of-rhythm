from datetime import UTC, datetime
from uuid import uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import (
    HistoricalKnowledgeDomainError,
    ListeningGuide,
    ListeningObservation,
)


def _observation(*, start: int | None = None, end: int | None = None) -> ListeningObservation:
    return ListeningObservation.create(
        "Ритм-секция",
        "Слушайте взаимодействие контрабаса и ударных.",
        uuid7(),
        datetime.now(UTC),
        start_seconds=start,
        end_seconds=end,
    )


def test_listening_guide_orders_observations_and_requires_one_for_publication() -> None:
    first, second = _observation(), _observation(start=5, end=12)
    guide = ListeningGuide.create_draft(uuid7(), (second, first))

    assert [item.position for item in guide.observations] == [1, 2]
    assert guide.publish().is_published
    with pytest.raises(HistoricalKnowledgeDomainError):
        ListeningGuide.create_draft(uuid7()).publish()


@pytest.mark.parametrize(("start", "end"), [(0, None), (3, 3), (-1, 2)])
def test_listening_observation_rejects_invalid_time_range(start: int | None, end: int | None) -> None:
    with pytest.raises(HistoricalKnowledgeDomainError):
        _observation(start=start, end=end)
