class MusicCatalogDomainError(ValueError):
    pass


class GenrePublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Genre cannot be published; missing: {', '.join(missing_fields)}")


class ClassificationAssignmentPublicationError(MusicCatalogDomainError):
    def __init__(self, invalid_fields: tuple[str, ...]) -> None:
        self.invalid_fields = invalid_fields
        super().__init__(f"Classification assignment cannot be published; invalid: {', '.join(invalid_fields)}")


class GroupPublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Group cannot be published; missing: {', '.join(missing_fields)}")
