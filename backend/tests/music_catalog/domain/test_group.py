from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    ExistencePeriod,
    Group,
    GroupContent,
    GroupMembership,
    GroupMembershipContent,
    MusicCatalogDomainError,
    TemporalBound,
    TemporalPrecision,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def test_group_content_normalizes_optional_values() -> None:
    period = ExistencePeriod.create(
        start=TemporalBound(1935, TemporalPrecision.EXACT_YEAR),
        end=TemporalBound(1945, TemporalPrecision.CIRCA_YEAR),
    )
    content = GroupContent.create(
        " Count Basie Orchestra ",
        aliases=(" Basie Band ",),
        description=" A swing orchestra. ",
        period=period,
    )

    assert content.canonical_name == "Count Basie Orchestra"
    assert content.aliases == ("Basie Band",)
    assert content.description == "A swing orchestra."
    assert content.period == period


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (lambda: GroupContent.create("Basie", aliases=("basie",)), "canonical name"),
        (lambda: GroupContent.create("Basie", aliases=("Band", "band")), "aliases must not contain"),
        (
            lambda: ExistencePeriod.create(
                start=TemporalBound(1950, TemporalPrecision.EXACT_YEAR),
                end=TemporalBound(1940, TemporalPrecision.EXACT_YEAR),
            ),
            "period start must not be later",
        ),
    ],
)
def test_group_value_objects_reject_invalid_content(content: Callable[[], object], message: str) -> None:
    with pytest.raises(MusicCatalogDomainError, match=message):
        content()


def test_group_publish_requires_only_canonical_name() -> None:
    group = Group.create(uuid7(), GroupContent.create("Charlie Parker Quintet"))
    published = group.publish()

    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert published.canonical_name == "Charlie Parker Quintet"


def test_group_membership_accepts_minimal_and_rich_content() -> None:
    minimal = GroupMembership.create(uuid7(), uuid7(), uuid7())
    rich = GroupMembership.create(
      uuid7(),
      uuid7(),
      uuid7(),
      GroupMembershipContent.create(
          period=ExistencePeriod.create(start=TemporalBound(1940, TemporalPrecision.EXACT_YEAR)),
          roles_or_instruments=("alto saxophone", "leader"),
          provenance="Editorial note.",
      ),
    )

    assert minimal.period is None
    assert minimal.roles_or_instruments == ()
    assert minimal.provenance is None
    assert rich.period is not None
    assert rich.roles_or_instruments == ("alto saxophone", "leader")
    assert rich.provenance == "Editorial note."


def test_group_membership_publish_without_roles_or_period() -> None:
    membership = GroupMembership.create(uuid7(), uuid7(), uuid7())
    published = membership.publish()

    assert published.editorial_status is EditorialStatus.PUBLISHED
