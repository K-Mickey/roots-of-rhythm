from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.application import GroupMembershipService, GroupService
from roots_of_rhythm.music_catalog.domain import (
    ExistencePeriod,
    GroupContent,
    GroupMembershipContent,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_group_and_membership_repositories_round_trip_and_filter_published(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    group_service = GroupService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    membership_service = GroupMembershipService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    period = ExistencePeriod.create(
        start=TemporalBound(1935, TemporalPrecision.EXACT_YEAR),
        end=TemporalBound(1950, TemporalPrecision.CIRCA_YEAR),
    )
    content = GroupContent.create(
        "Benny Goodman Orchestra",
        aliases=("BGO",),
        description="A swing orchestra.",
        period=period,
    )
    published = await group_service.create(content)
    duplicate = await group_service.create(GroupContent.create("Benny Goodman Orchestra"))
    await group_service.publish(published.id)
    await group_service.publish(duplicate.id)
    archived = await group_service.create(GroupContent.create("Archived Group"))
    await group_service.publish(archived.id)
    await group_service.archive(archived.id)
    draft = await group_service.create(GroupContent.create("Draft Group"))
    empty_group = await group_service.create(GroupContent.create("Tympany Five"))
    await group_service.publish(empty_group.id)

    membership = await membership_service.create(
        uuid7(),
        empty_group.id,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(start=TemporalBound(1940, TemporalPrecision.EXACT_YEAR)),
            roles_or_instruments=("vocals", "saxophone"),
            provenance="Seed editorial note.",
        ),
    )
    await membership_service.publish(membership.id)
    draft_membership = await membership_service.create(uuid7(), empty_group.id)
    await membership_service.publish(draft_membership.id)
    await membership_service.archive(draft_membership.id)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.groups.get_published(published.id)
        listed = await uow.groups.list_published()
        memberships = await uow.group_memberships.list_published_by_group(empty_group.id)

    assert loaded is not None
    assert loaded.canonical_name == content.canonical_name
    assert loaded.aliases == content.aliases
    assert loaded.description == content.description
    assert loaded.period == content.period
    assert {group.id for group in listed} == {published.id, duplicate.id, empty_group.id}
    assert draft.id not in {group.id for group in listed}
    assert archived.id not in {group.id for group in listed}
    assert len(memberships) == 1
    assert memberships[0].roles_or_instruments == ("vocals", "saxophone")
    assert memberships[0].provenance == "Seed editorial note."

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        await uow.groups.mark_deleted(published.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.groups.get(published.id) is None
        assert await uow.groups.get_published(published.id) is None
