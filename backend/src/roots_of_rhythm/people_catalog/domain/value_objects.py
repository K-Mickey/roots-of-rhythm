from urllib.parse import urlsplit

import msgspec

from roots_of_rhythm.people_catalog.domain.enums import TemporalPrecision
from roots_of_rhythm.people_catalog.domain.errors import PeopleCatalogDomainError
from roots_of_rhythm.text_lengths import TEXT_64, TEXT_1024, TEXT_2048


def _required_text(value: str, field: str, *, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise PeopleCatalogDomainError(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise PeopleCatalogDomainError(f"{field} must be at most {max_length} characters")
    return normalized


def _optional_text(value: str | None, field: str, *, max_length: int) -> str | None:
    return None if value is None else _required_text(value, field, max_length=max_length)


def _unique_texts(values: tuple[str, ...], field: str, *, max_length: int) -> tuple[str, ...]:
    normalized = tuple(_required_text(value, field, max_length=max_length) for value in values)
    folded = tuple(value.casefold() for value in normalized)
    if len(folded) != len(set(folded)):
        raise PeopleCatalogDomainError(f"{field} must not contain duplicates")
    return normalized


class PersonDate(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecision


class ExternalIdentity(msgspec.Struct, frozen=True):
    provider: str
    identifier: str
    url: str | None = None

    @classmethod
    def create(cls, provider: str, identifier: str, *, url: str | None = None) -> "ExternalIdentity":
        normalized_url = _optional_text(url, "external identity URL", max_length=TEXT_2048)
        if normalized_url is not None:
            parsed = urlsplit(normalized_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise PeopleCatalogDomainError("external identity URL must use http or https")
        return cls(
            provider=_required_text(provider, "external identity provider", max_length=TEXT_64),
            identifier=_required_text(identifier, "external identity identifier", max_length=TEXT_64),
            url=normalized_url,
        )


class PersonContent(msgspec.Struct, frozen=True):
    canonical_name: str
    aliases: tuple[str, ...] = ()
    biography: str | None = None
    birth_date: PersonDate | None = None
    death_date: PersonDate | None = None
    external_identities: tuple[ExternalIdentity, ...] = ()

    @classmethod
    def create(
        cls,
        canonical_name: str,
        *,
        aliases: tuple[str, ...] = (),
        biography: str | None = None,
        birth_date: PersonDate | None = None,
        death_date: PersonDate | None = None,
        external_identities: tuple[ExternalIdentity, ...] = (),
    ) -> "PersonContent":
        normalized_name = _required_text(canonical_name, "canonical name", max_length=TEXT_64)
        normalized_aliases = _unique_texts(aliases, "aliases", max_length=TEXT_64)
        if normalized_name.casefold() in {alias.casefold() for alias in normalized_aliases}:
            raise PeopleCatalogDomainError("aliases must not duplicate the canonical name")
        normalized_identities = tuple(
            ExternalIdentity.create(identity.provider, identity.identifier, url=identity.url)
            for identity in external_identities
        )
        identity_keys = tuple(
            (identity.provider.casefold(), identity.identifier.casefold()) for identity in normalized_identities
        )
        if len(identity_keys) != len(set(identity_keys)):
            raise PeopleCatalogDomainError("external identities must not contain duplicates")
        if birth_date is not None and death_date is not None and birth_date.year > death_date.year:
            raise PeopleCatalogDomainError("birth year must not be later than death year")
        return cls(
            canonical_name=normalized_name,
            aliases=normalized_aliases,
            biography=_optional_text(biography, "biography", max_length=TEXT_1024),
            birth_date=birth_date,
            death_date=death_date,
            external_identities=normalized_identities,
        )
