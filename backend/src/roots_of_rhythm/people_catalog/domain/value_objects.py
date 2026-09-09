import msgspec

from roots_of_rhythm.people_catalog.domain.enums import TemporalPrecision
from roots_of_rhythm.people_catalog.domain.errors import PeopleCatalogDomainError
from roots_of_rhythm.utils.text import is_http_url, optional_text, required_text, unique_texts
from roots_of_rhythm.utils.text_lengths import TEXT_64, TEXT_1024, TEXT_2048


class PersonDate(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecision


class ExternalIdentity(msgspec.Struct, frozen=True):
    provider: str
    identifier: str
    url: str | None = None

    @classmethod
    def create(cls, provider: str, identifier: str, *, url: str | None = None) -> "ExternalIdentity":
        normalized_url = optional_text(
            url, "external identity URL", max_length=TEXT_2048, error=PeopleCatalogDomainError
        )
        if normalized_url is not None and not is_http_url(normalized_url):
            raise PeopleCatalogDomainError("external identity URL must use http or https")
        return cls(
            provider=required_text(
                provider, "external identity provider", max_length=TEXT_64, error=PeopleCatalogDomainError
            ),
            identifier=required_text(
                identifier, "external identity identifier", max_length=TEXT_64, error=PeopleCatalogDomainError
            ),
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
        normalized_name = required_text(
            canonical_name, "canonical name", max_length=TEXT_64, error=PeopleCatalogDomainError
        )
        normalized_aliases = unique_texts(aliases, "aliases", max_length=TEXT_64, error=PeopleCatalogDomainError)
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
            biography=optional_text(biography, "biography", max_length=TEXT_1024, error=PeopleCatalogDomainError),
            birth_date=birth_date,
            death_date=death_date,
            external_identities=normalized_identities,
        )
