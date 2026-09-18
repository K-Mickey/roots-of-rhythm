class GenreNotFound(LookupError):
    pass


class GenreNameConflict(ValueError):
    pass


class ClassificationAssignmentNotFound(LookupError):
    pass


class ClassificationAssignmentConflict(ValueError):
    pass


class ClassificationAssignmentPersonNotPublished(ValueError):
    pass


class ClassificationAssignmentGroupNotPublished(ValueError):
    pass


class ClassificationAssignmentGenreNotPublished(ValueError):
    pass


class ClassificationAssignmentTargetUnsupported(ValueError):
    pass


class GroupNotFound(LookupError):
    pass


class GroupMembershipNotFound(LookupError):
    pass


class MusicalWorkNotFound(LookupError):
    pass


class WorkCreditNotFound(LookupError):
    pass


class WorkCreditConflict(ValueError):
    pass


class WorkRelationNotFound(LookupError):
    pass


class WorkRelationConflict(ValueError):
    pass


class WorkRelationWorkNotPublished(ValueError):
    pass


class LyricsVersionNotFound(LookupError):
    pass


class LyricsVersionConflict(ValueError):
    pass


class LyricsVersionCreditNotFound(LookupError):
    pass


class LyricsVersionCreditConflict(ValueError):
    pass


class LyricsVersionRelationNotFound(LookupError):
    pass


class LyricsVersionRelationConflict(ValueError):
    pass


class LyricsVersionEndpointNotPublished(ValueError):
    pass


class RecordingNotFound(LookupError):
    pass


class RecordingConflict(ValueError):
    pass


class RecordingWorkNotPublished(ValueError):
    pass


class RecordingPrimaryTargetNotPublished(ValueError):
    pass


class RecordingLyricsVersionNotPublished(ValueError):
    pass


class RecordingLyricsVersionNotPerformable(ValueError):
    pass


class RecordingLyricsVersionWorkMismatch(ValueError):
    pass
