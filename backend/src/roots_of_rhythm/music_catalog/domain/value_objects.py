from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import TemporalPrecision
from roots_of_rhythm.music_catalog.domain.errors import MusicCatalogDomainError

SHORT_TEXT_MAX_LENGTH = 64
LONG_TEXT_MAX_LENGTH = 1024


def _required_text(value: str, field: str, *, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise MusicCatalogDomainError(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise MusicCatalogDomainError(f"{field} must be at most {max_length} characters")
    return normalized


def optional_text(value: str | None, field: str, *, max_length: int) -> str | None:
    return None if value is None else _required_text(value, field, max_length=max_length)


def _unique_texts(values: tuple[str, ...], field: str, *, max_length: int) -> tuple[str, ...]:
    normalized = tuple(_required_text(value, field, max_length=max_length) for value in values)
    folded = tuple(value.casefold() for value in normalized)
    if len(folded) != len(set(folded)):
        raise MusicCatalogDomainError(f"{field} must not contain duplicates")
    return normalized


class TemporalBound(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecision


class HistoricalPeriod(msgspec.Struct, frozen=True):
    label: str
    start: TemporalBound | None = None
    end: TemporalBound | None = None

    @classmethod
    def create(
        cls,
        label: str,
        start: TemporalBound | None = None,
        end: TemporalBound | None = None,
    ) -> "HistoricalPeriod":
        if start is not None and end is not None and start.year > end.year:
            raise MusicCatalogDomainError("period start must not be later than period end")
        return cls(
            label=_required_text(label, "period label", max_length=SHORT_TEXT_MAX_LENGTH),
            start=start,
            end=end,
        )


class GeographicContext(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "GeographicContext":
        return cls(summary=_required_text(summary, "geographic summary", max_length=SHORT_TEXT_MAX_LENGTH))


class ClassificationContent(msgspec.Struct, frozen=True):
    canonical_name: str
    aliases: tuple[str, ...] = ()
    definition: str | None = None
    boundaries: str | None = None
    period: HistoricalPeriod | None = None
    geography: GeographicContext | None = None
    historical_context: str | None = None
    formation: str | None = None
    characteristic_features: tuple[str, ...] = ()
    primary_image_id: UUID | None = None

    @classmethod
    def create(
        cls,
        canonical_name: str,
        *,
        aliases: tuple[str, ...] = (),
        definition: str | None = None,
        boundaries: str | None = None,
        period: HistoricalPeriod | None = None,
        geography: GeographicContext | None = None,
        historical_context: str | None = None,
        formation: str | None = None,
        characteristic_features: tuple[str, ...] = (),
        primary_image_id: UUID | None = None,
    ) -> "ClassificationContent":
        normalized_name = _required_text(
            canonical_name,
            "canonical name",
            max_length=SHORT_TEXT_MAX_LENGTH,
        )
        normalized_aliases = _unique_texts(aliases, "aliases", max_length=SHORT_TEXT_MAX_LENGTH)
        if normalized_name.casefold() in {alias.casefold() for alias in normalized_aliases}:
            raise MusicCatalogDomainError("aliases must not duplicate the canonical name")
        return cls(
            canonical_name=normalized_name,
            aliases=normalized_aliases,
            definition=optional_text(definition, "definition", max_length=LONG_TEXT_MAX_LENGTH),
            boundaries=optional_text(boundaries, "boundaries", max_length=LONG_TEXT_MAX_LENGTH),
            period=period,
            geography=geography,
            historical_context=optional_text(
                historical_context,
                "historical context",
                max_length=LONG_TEXT_MAX_LENGTH,
            ),
            formation=optional_text(formation, "formation", max_length=LONG_TEXT_MAX_LENGTH),
            characteristic_features=_unique_texts(
                characteristic_features,
                "characteristic features",
                max_length=SHORT_TEXT_MAX_LENGTH,
            ),
            primary_image_id=primary_image_id,
        )
