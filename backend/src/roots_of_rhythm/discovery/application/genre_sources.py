from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.genres import GenreSourcesResponse, SourceView
from roots_of_rhythm.discovery.application.errors.genres import (
    GenreSourcesAssemblyError,
    GenreSourcesNotFound,
)
from roots_of_rhythm.discovery.application.genre_relation_projection import (
    GenreRelationProjectionError,
    ordered_public_claims_for_page,
    related_genre_id,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.source_service import SourceService
    from roots_of_rhythm.historical_knowledge.domain import Source
    from roots_of_rhythm.historical_knowledge.public import PublishedGenreRelationClaimReader
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

type MusicCatalogUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GenreSourcesReader(Protocol):
    async def get(self, genre_id: UUID) -> GenreSourcesResponse: ...


class GenreSourcesQuery:
    def __init__(
        self,
        music_uow_factory: MusicCatalogUnitOfWorkFactory,
        genre_relation_claim_reader: PublishedGenreRelationClaimReader,
        source_service: SourceService,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._genre_relation_claim_reader = genre_relation_claim_reader
        self._source_service = source_service

    async def get(self, genre_id: UUID) -> GenreSourcesResponse:
        async with self._music_uow_factory() as uow:
            anchor = await uow.genres.get_published(genre_id)
        if anchor is None:
            raise GenreSourcesNotFound(str(genre_id))

        claim_data = await self._genre_relation_claim_reader.read_for_genre(genre_id)
        claims = claim_data.claims
        if not claims:
            return GenreSourcesResponse(genre_id=str(genre_id), sources=[])

        try:
            related_ids = {related_genre_id(claim, genre_id) for claim in claims}
        except GenreRelationProjectionError as error:
            raise GenreSourcesAssemblyError(str(error)) from error

        async with self._music_uow_factory() as uow:
            related_genres = await uow.genres.get_published_by_ids(related_ids)
        claims = tuple(claim for claim in claims if related_genre_id(claim, genre_id) in related_genres)
        try:
            ordered_claims = ordered_public_claims_for_page(
                claims,
                page_genre_id=genre_id,
                related_genres=related_genres,
            )
        except GenreRelationProjectionError as error:
            raise GenreSourcesAssemblyError(str(error)) from error

        ordered_source_ids: list[UUID] = []
        seen: set[UUID] = set()
        for claim in ordered_claims:
            for reference in claim_data.evidence_by_claim.get(claim.id, ()):
                if reference.source_id in seen:
                    continue
                seen.add(reference.source_id)
                ordered_source_ids.append(reference.source_id)

        if not ordered_source_ids:
            return GenreSourcesResponse(genre_id=str(genre_id), sources=[])

        sources = await self._source_service.get_sources_by_ids(ordered_source_ids)
        if len(sources) != len(ordered_source_ids):
            raise GenreSourcesAssemblyError("public citation is missing a Source")

        return GenreSourcesResponse(
            genre_id=str(genre_id),
            sources=[_map_source(sources[source_id]) for source_id in ordered_source_ids],
        )


def _map_source(source: Source) -> SourceView:
    return SourceView(
        id=str(source.id),
        title=source.title,
        author=source.author,
        responsible_organization=source.responsible_organization,
        publication=source.publication,
        publication_date=source.publication_date,
        external_url=source.external_url,
    )
