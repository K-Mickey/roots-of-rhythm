class ClaimNotFound(LookupError):
    pass


class SourceNotFound(LookupError):
    pass


class EndpointGenreNotPublished(ValueError):
    pass


class EndpointGenreMissing(ValueError):
    pass


class EvidenceFragmentNotReviewed(ValueError):
    pass


class EndpointWorkMissing(ValueError):
    pass


class EndpointWorkNotPublished(ValueError):
    pass


class EndpointRecordingMissing(ValueError):
    pass


class EndpointRecordingNotPublished(ValueError):
    pass


class UniqueConstraintViolation(Exception):
    def __init__(self, constraint_name: str | None = None) -> None:
        self.constraint_name = constraint_name
        super().__init__(constraint_name or "unique constraint violated")


class ListeningGuideNotFound(LookupError):
    pass


class ListeningGuideRecordingNotPublished(ValueError):
    pass
