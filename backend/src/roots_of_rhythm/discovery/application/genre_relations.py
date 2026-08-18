from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import (
    EvidenceReferenceView,
    GenreRelationsResponse,
    GenreRelationView,
    GenreSummary,
    GeographicContextView,
    RelationHistoricalPeriodView,
    RelationPerspective,
    RelationTemporalBoundView,
)
from roots_of_rhythm.discovery.application.errors import (
    GenreRelationsAssemblyError,
    GenreRelationsNotFound,
)
from roots_of_rhythm.historical_knowledge.domain import (
    GenreRelationClaim,
    RelationType,
    TemporalPrecision,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.claim_service import ClaimService, PublicEvidenceReference
    from roots_of_rhythm.historical_knowledge.domain import GeographicContext, HistoricalPeriod, TemporalBound
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
        claim_service: ClaimService,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._claim_service = claim_service

    async def get(self, genre_id: UUID) -> GenreRelationsResponse:
        async with self._music_uow_factory() as uow:
            anchor = await uow.genres.get_published(genre_id)
        if anchor is None:
            raise GenreRelationsNotFound(str(genre_id))

        claims = await self._claim_service.list_public_for_genre(genre_id)
        if not claims:
            return GenreRelationsResponse(genre_id=str(genre_id), relations=[])

        related_ids = {_related_genre_id(claim, genre_id) for claim in claims}
        async with self._music_uow_factory() as uow:
            related_genres = await uow.genres.get_published_by_ids(related_ids)
        if len(related_genres) != len(related_ids):
            raise GenreRelationsAssemblyError("visible relation is missing a published related Genre")

        evidence_by_claim = await self._claim_service.public_evidence_references_for_claims(claims)
        views = [
            _map_relation(
                claim,
                page_genre_id=genre_id,
                related_genres=related_genres,
                evidence=evidence_by_claim.get(claim.id, ()),
            )
            for claim in claims
        ]
        return GenreRelationsResponse(
            genre_id=str(genre_id),
            relations=_sort_relations(views),
        )


def _relation_perspective(claim: GenreRelationClaim, page_genre_id: UUID) -> RelationPerspective:
    _ensure_page_endpoint(claim, page_genre_id)
    if claim.relation_type is RelationType.OVERLAPS_WITH:
        return RelationPerspective.SYMMETRIC
    if claim.subject_genre_id == page_genre_id:
        return RelationPerspective.SUBJECT
    return RelationPerspective.TARGET


def _related_genre_id(claim: GenreRelationClaim, page_genre_id: UUID) -> UUID:
    _ensure_page_endpoint(claim, page_genre_id)
    if claim.subject_genre_id == page_genre_id:
        return claim.target_genre_id
    return claim.subject_genre_id


def _ensure_page_endpoint(claim: GenreRelationClaim, page_genre_id: UUID) -> None:
    if page_genre_id not in (claim.subject_genre_id, claim.target_genre_id):
        raise GenreRelationsAssemblyError("page Genre is not an endpoint of the visible relation")


def _map_relation(
    claim: GenreRelationClaim,
    *,
    page_genre_id: UUID,
    related_genres: Mapping[UUID, Genre],
    evidence: Sequence[PublicEvidenceReference],
) -> GenreRelationView:
    related_id = _related_genre_id(claim, page_genre_id)
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


def _sort_relations(views: list[GenreRelationView]) -> list[GenreRelationView]:
    relation_type_order = {value: index for index, value in enumerate(RelationType)}
    precision_order = {value: index for index, value in enumerate(TemporalPrecision)}

    def sort_key(view: GenreRelationView) -> tuple[bool, int, int, int, str]:
        start = None if view.temporal_context is None else view.temporal_context.start
        year = 0 if start is None else start.year
        precision_rank = 0 if start is None else precision_order[start.precision]
        type_rank = relation_type_order[view.relation_type]
        return (start is None, year, precision_rank, type_rank, view.related_genre.name.casefold())

    return sorted(views, key=sort_key)
