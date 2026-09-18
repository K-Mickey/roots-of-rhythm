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


class ListeningGuideNotFound(LookupError):
    pass


class ListeningGuideRecordingNotPublished(ValueError):
    pass
