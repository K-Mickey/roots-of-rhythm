from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import EvidenceRole, GenreRelationClaim


@dataclass(frozen=True, slots=True)
class PublicEvidenceReference:
    source_id: UUID
    role: EvidenceRole
    locator_text: str | None
    external_url: str | None


@dataclass(frozen=True, slots=True)
class PublishedGenreRelationClaims:
    claims: tuple[GenreRelationClaim, ...]
    evidence_by_claim: Mapping[UUID, tuple[PublicEvidenceReference, ...]]


class PublishedGenreRelationClaimReader(Protocol):
    async def read_for_genre(self, genre_id: UUID) -> PublishedGenreRelationClaims: ...
