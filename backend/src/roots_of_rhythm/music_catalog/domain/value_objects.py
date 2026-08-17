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


def _optional_text(value: str | None, field: str, *, max_length: int) -> str | None:
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

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _required_text(self.label, "period label", max_length=SHORT_TEXT_MAX_LENGTH),
        )
        if self.start is not None and self.end is not None and self.start.year > self.end.year:
            raise MusicCatalogDomainError("period start must not be later than period end")


class GeographicContext(msgspec.Struct, frozen=True):
    summary: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "summary",
            _required_text(self.summary, "geographic summary", max_length=SHORT_TEXT_MAX_LENGTH),
        )


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

    def __post_init__(self) -> None:
        canonical_name = _required_text(
            self.canonical_name,
            "canonical name",
            max_length=SHORT_TEXT_MAX_LENGTH,
        )
        aliases = _unique_texts(self.aliases, "aliases", max_length=SHORT_TEXT_MAX_LENGTH)
        if canonical_name.casefold() in {alias.casefold() for alias in aliases}:
            raise MusicCatalogDomainError("aliases must not duplicate the canonical name")

        object.__setattr__(self, "canonical_name", canonical_name)
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(
            self,
            "definition",
            _optional_text(self.definition, "definition", max_length=LONG_TEXT_MAX_LENGTH),
        )
        object.__setattr__(
            self,
            "boundaries",
            _optional_text(self.boundaries, "boundaries", max_length=LONG_TEXT_MAX_LENGTH),
        )
        object.__setattr__(
            self,
            "historical_context",
            _optional_text(self.historical_context, "historical context", max_length=LONG_TEXT_MAX_LENGTH),
        )
        object.__setattr__(
            self,
            "formation",
            _optional_text(self.formation, "formation", max_length=LONG_TEXT_MAX_LENGTH),
        )
        object.__setattr__(
            self,
            "characteristic_features",
            _unique_texts(
                self.characteristic_features,
                "characteristic features",
                max_length=SHORT_TEXT_MAX_LENGTH,
            ),
        )
