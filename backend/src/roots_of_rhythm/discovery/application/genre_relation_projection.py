from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.domain import GenreRelationClaim, RelationType, TemporalPrecision

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Genre


class GenreRelationProjectionError(Exception):
    """Public Genre relation projection cannot be assembled from the current claim set."""


def related_genre_id(claim: GenreRelationClaim, page_genre_id: UUID) -> UUID:
    ensure_page_endpoint(claim, page_genre_id)
    if claim.subject_genre_id == page_genre_id:
        return claim.target_genre_id
    return claim.subject_genre_id


def ensure_page_endpoint(claim: GenreRelationClaim, page_genre_id: UUID) -> None:
    if page_genre_id not in (claim.subject_genre_id, claim.target_genre_id):
        raise GenreRelationProjectionError("page Genre is not an endpoint of the visible relation")


def ordered_public_claims_for_page(
    claims: Sequence[GenreRelationClaim],
    *,
    page_genre_id: UUID,
    related_genres: Mapping[UUID, Genre],
) -> list[GenreRelationClaim]:
    relation_type_order = {value: index for index, value in enumerate(RelationType)}
    precision_order = {value: index for index, value in enumerate(TemporalPrecision)}

    def sort_key(claim: GenreRelationClaim) -> tuple[bool, int, int, int, str]:
        start = None if claim.temporal is None else claim.temporal.start
        year = 0 if start is None else start.year
        precision_rank = 0 if start is None else precision_order[start.precision]
        type_rank = relation_type_order[claim.relation_type]
        related = related_genres[related_genre_id(claim, page_genre_id)]
        return (start is None, year, precision_rank, type_rank, related.content.canonical_name.casefold())

    return sorted(claims, key=sort_key)
