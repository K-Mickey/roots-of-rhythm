class MusicCatalogDomainError(ValueError):
    pass


class GenrePublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Genre cannot be published; missing: {', '.join(missing_fields)}")
