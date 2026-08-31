from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    GeographicContextView,
    RelationHistoricalPeriodView,
    RelationPerspective,
    RelationTemporalBoundView,
)
from roots_of_rhythm.discovery.application.dto.genres import (
    EvidenceReferenceView,
    GenreRelationsResponse,
    GenreRelationView,
)
from roots_of_rhythm.discovery.application.errors.genres import (
    GenreRelationsAssemblyError,
    GenreRelationsNotFound,
)
from roots_of_rhythm.discovery.application.genre_relation_projection import (
    GenreRelationProjectionError,
    ensure_page_endpoint,
    ordered_public_claims_for_page,
    related_genre_id,
)
from roots_of_rhythm.historical_knowledge.domain import GenreRelationClaim, RelationType

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import GeographicContext, HistoricalPeriod, TemporalBound
    from roots_of_rhythm.historical_knowledge.public import (
        PublicEvidenceReference,
        PublishedGenreRelationClaimReader,
    )
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.music_catalog.domain import Genre

type MusicCatalogUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GenreRelationsReader(Protocol):
    async def get(self, genre_id: UUID) -> GenreRelationsResponse: ...


class GenreRelationsQuery:
    def __init__(
        self,
        music_uow_factory: MusicCatalogUnitOfWorkFactory,
        genre_relation_claim_reader: PublishedGenreRelationClaimReader,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._genre_relation_claim_reader = genre_relation_claim_reader

    async def get(self, genre_id: UUID) -> GenreRelationsResponse:
        async with self._music_uow_factory() as uow:
            anchor = await uow.genres.get_published(genre_id)
        if anchor is None:
            raise GenreRelationsNotFound(str(genre_id))

        claim_data = await self._genre_relation_claim_reader.read_for_genre(genre_id)
        claims = claim_data.claims
        if not claims:
            return GenreRelationsResponse(genre_id=str(genre_id), relations=[])

        try:
            related_ids = {related_genre_id(claim, genre_id) for claim in claims}
        except GenreRelationProjectionError as error:
            raise GenreRelationsAssemblyError(str(error)) from error

        async with self._music_uow_factory() as uow:
            related_genres = await uow.genres.get_published_by_ids(related_ids)
        claims = tuple(claim for claim in claims if related_genre_id(claim, genre_id) in related_genres)
        try:
            ordered = ordered_public_claims_for_page(
                claims,
                page_genre_id=genre_id,
                related_genres=related_genres,
            )
            return GenreRelationsResponse(
                genre_id=str(genre_id),
                relations=[
                    _map_relation(
                        claim,
                        page_genre_id=genre_id,
                        related_genres=related_genres,
                        evidence=claim_data.evidence_by_claim.get(claim.id, ()),
                    )
                    for claim in ordered
                ],
            )
        except GenreRelationProjectionError as error:
            raise GenreRelationsAssemblyError(str(error)) from error


def _relation_perspective(claim: GenreRelationClaim, page_genre_id: UUID) -> RelationPerspective:
    ensure_page_endpoint(claim, page_genre_id)
    if claim.relation_type is RelationType.OVERLAPS_WITH:
        return RelationPerspective.SYMMETRIC
    if claim.subject_genre_id == page_genre_id:
        return RelationPerspective.SUBJECT
    return RelationPerspective.TARGET


def _map_relation(
    claim: GenreRelationClaim,
    *,
    page_genre_id: UUID,
    related_genres: Mapping[UUID, Genre],
    evidence: Sequence[PublicEvidenceReference],
) -> GenreRelationView:
    related_id = related_genre_id(claim, page_genre_id)
    related = related_genres[related_id]
    if claim.explanation is None:
        raise GenreRelationsAssemblyError("published relation is missing explanation")
    return GenreRelationView(
        id=str(claim.id),
        related_genre=GenreSummary(id=str(related.id), name=related.content.canonical_name),
        relation_type=claim.relation_type,
        perspective=_relation_perspective(claim, page_genre_id),
        explanation=claim.explanation,
        temporal_context=_map_period(claim.temporal),
        geographic_context=_map_geography(claim.geographic),
        evidence_status=claim.evidence_status,
        evidence_references=[
            EvidenceReferenceView(
                source_id=str(item.source_id),
                role=item.role,
                locator_text=item.locator_text,
                external_url=item.external_url,
            )
            for item in evidence
        ],
    )


def _map_period(period: HistoricalPeriod | None) -> RelationHistoricalPeriodView | None:
    if period is None:
        return None
    return RelationHistoricalPeriodView(
        label=period.label,
        start=_map_bound(period.start),
        end=_map_bound(period.end),
    )


def _map_bound(bound: TemporalBound | None) -> RelationTemporalBoundView | None:
    if bound is None:
        return None
    return RelationTemporalBoundView(year=bound.year, precision=bound.precision)


def _map_geography(geography: GeographicContext | None) -> GeographicContextView | None:
    if geography is None:
        return None
    return GeographicContextView(summary=geography.summary)
