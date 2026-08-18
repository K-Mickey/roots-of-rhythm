from collections.abc import Callable, Collection
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application.errors import SourceNotFound
from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
from roots_of_rhythm.historical_knowledge.domain import Source, SourceFragment, SourceVersion

if TYPE_CHECKING:
    from uuid import UUID

type UnitOfWorkFactory = Callable[[], HistoricalKnowledgeUnitOfWork]


class SourceService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create_source(
        self,
        title: str,
        *,
        author: str | None = None,
        responsible_organization: str | None = None,
        publication: str | None = None,
        publication_date: str | None = None,
        external_url: str | None = None,
        source_id: UUID | None = None,
    ) -> Source:
        source = Source.create(
            title,
            author=author,
            responsible_organization=responsible_organization,
            publication=publication,
            publication_date=publication_date,
            external_url=external_url,
            source_id=source_id,
        )
        async with self._uow_factory() as uow:
            await uow.sources.add_source(source)
            await uow.commit()
            return source

    async def create_version(
        self,
        source_id: UUID,
        label: str,
        *,
        version_id: UUID | None = None,
    ) -> SourceVersion:
        async with self._uow_factory() as uow:
            if await uow.sources.get_source(source_id) is None:
                raise SourceNotFound(str(source_id))
            version = SourceVersion.create(source_id, label, version_id=version_id)
            await uow.sources.add_version(version)
            await uow.commit()
            return version

    async def create_fragment(
        self,
        source_version_id: UUID,
        *,
        locator_text: str | None = None,
        external_url: str | None = None,
        fragment_id: UUID | None = None,
    ) -> SourceFragment:
        async with self._uow_factory() as uow:
            if await uow.sources.get_version(source_version_id) is None:
                raise SourceNotFound(str(source_version_id))
            fragment = SourceFragment.create(
                source_version_id,
                locator_text=locator_text,
                external_url=external_url,
                fragment_id=fragment_id,
            )
            await uow.sources.add_fragment(fragment)
            await uow.commit()
            return fragment

    async def mark_fragment_reviewed(self, fragment_id: UUID) -> SourceFragment:
        async with self._uow_factory() as uow:
            fragment = await uow.sources.get_fragment(fragment_id)
            if fragment is None:
                raise SourceNotFound(str(fragment_id))
            reviewed = fragment.mark_reviewed()
            await uow.sources.save_fragment(reviewed)
            await uow.commit()
            return reviewed

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        async with self._uow_factory() as uow:
            return await uow.sources.get_sources_by_ids(source_ids)
