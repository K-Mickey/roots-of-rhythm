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


class MusicalWorkPublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"MusicalWork cannot be published; missing: {', '.join(missing_fields)}")


class WorkRelationPublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"WorkRelation cannot be published; missing: {', '.join(missing_fields)}")


class WorkRelationSelfReferenceError(MusicCatalogDomainError):
    def __init__(self) -> None:
        super().__init__("WorkRelation source and target must differ")


class LyricsVersionPublicationError(MusicCatalogDomainError):
    def __init__(self, invalid_fields: tuple[str, ...]) -> None:
        self.invalid_fields = invalid_fields
        super().__init__(f"LyricsVersion cannot be published; invalid: {', '.join(invalid_fields)}")


class LyricsVersionInvalidCombinationError(MusicCatalogDomainError):
    def __init__(self) -> None:
        super().__init__("machine translation cannot be performable")


class LyricsVersionRelationPublicationError(MusicCatalogDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"LyricsVersionRelation cannot be published; missing: {', '.join(missing_fields)}")


class LyricsVersionRelationSelfReferenceError(MusicCatalogDomainError):
    def __init__(self) -> None:
        super().__init__("LyricsVersionRelation source and target must differ")
