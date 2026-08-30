import msgspec

from roots_of_rhythm.discovery.application.dto.common import (
    ExternalIdentityView,
    GenreSummary,
    PerformerSummary,
    PersonDateView,
    PublicImageView,
)


class PerformerListResponse(msgspec.Struct, frozen=True):
    items: list[PerformerSummary]


class PerformerOverviewResponse(msgspec.Struct, frozen=True):
    id: str
    name: str
    aliases: list[str]
    biography: str | None
    birth_date: PersonDateView | None
    death_date: PersonDateView | None
    external_identities: list[ExternalIdentityView]
    primary_image: PublicImageView | None
    genres: list[GenreSummary]
