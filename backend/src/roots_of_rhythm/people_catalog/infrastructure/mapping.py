from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus,
    ExternalIdentity,
    Person,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord


def record_from_person(person: Person) -> PersonRecord:
    birth_date = person.birth_date
    death_date = person.death_date
    return PersonRecord(
        id=person.id,
        editorial_status=person.editorial_status.value,
        canonical_name=person.canonical_name,
        aliases=list(person.aliases),
        biography=person.biography,
        birth_year=birth_date.year if birth_date is not None else None,
        birth_precision=birth_date.precision.value if birth_date is not None else None,
        death_year=death_date.year if death_date is not None else None,
        death_precision=death_date.precision.value if death_date is not None else None,
        external_identities=[
            {"provider": identity.provider, "identifier": identity.identifier, "url": identity.url}
            for identity in person.external_identities
        ],
    )


def person_from_record(record: PersonRecord) -> Person:
    return Person.create(
        record.id,
        PersonContent.create(
            record.canonical_name,
            aliases=tuple(record.aliases),
            biography=record.biography,
            birth_date=_person_date(record.birth_year, record.birth_precision),
            death_date=_person_date(record.death_year, record.death_precision),
            external_identities=tuple(
                ExternalIdentity.create(
                    identity["provider"],
                    identity["identifier"],
                    url=identity["url"],
                )
                for identity in record.external_identities
            ),
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_record(record: PersonRecord, person: Person) -> None:
    birth_date = person.birth_date
    death_date = person.death_date
    record.editorial_status = person.editorial_status.value
    record.canonical_name = person.canonical_name
    record.aliases = list(person.aliases)
    record.biography = person.biography
    record.birth_year = birth_date.year if birth_date is not None else None
    record.birth_precision = birth_date.precision.value if birth_date is not None else None
    record.death_year = death_date.year if death_date is not None else None
    record.death_precision = death_date.precision.value if death_date is not None else None
    record.external_identities = [
        {"provider": identity.provider, "identifier": identity.identifier, "url": identity.url}
        for identity in person.external_identities
    ]


def _person_date(year: int | None, precision: str | None) -> PersonDate | None:
    if year is None or precision is None:
        return None
    return PersonDate(year=year, precision=TemporalPrecision(precision))
