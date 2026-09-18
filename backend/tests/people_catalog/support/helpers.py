from uuid import uuid7

from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent


def create_person(name: str, status: EditorialStatus = EditorialStatus.PUBLISHED) -> Person:
    return Person.create(uuid7(), PersonContent.create(name), editorial_status=status)
