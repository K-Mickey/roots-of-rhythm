from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class PeopleCatalogDomainError(ValueError):
    pass


class PersonNotFound(PeopleCatalogDomainError):
    pass


class PersonAlreadyExistsError(PeopleCatalogDomainError):
    def __init__(self, id_: UUID) -> None:
        super().__init__(f"Person already exists id={id_}")


class PersonPublicationError(PeopleCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Person cannot be published; missing: {', '.join(missing_fields)}")
