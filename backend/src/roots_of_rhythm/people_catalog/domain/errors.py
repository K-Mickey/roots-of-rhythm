class PeopleCatalogDomainError(ValueError):
    pass


class PersonPublicationError(PeopleCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Person cannot be published; missing: {', '.join(missing_fields)}")
