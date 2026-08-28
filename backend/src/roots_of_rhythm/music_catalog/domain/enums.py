from enum import StrEnum


class ClassificationKind(StrEnum):
    GENRE = "genre"
    STYLE = "style"
    SCENE = "scene"
    TRADITION = "tradition"


class EditorialStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TemporalPrecision(StrEnum):
    EXACT_YEAR = "exact_year"
    CIRCA_YEAR = "circa_year"
    DECADE = "decade"
    EARLY_DECADE = "early_decade"
    MID_DECADE = "mid_decade"
    LATE_DECADE = "late_decade"


class ClassificationTargetKind(StrEnum):
    PERSON = "person"
    GROUP = "group"
    MUSICAL_WORK = "musical_work"
    RECORDING = "recording"
    RELEASE = "release"


class EvidenceStatus(StrEnum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    DISPUTED = "disputed"


class WorkCreditRole(StrEnum):
    COMPOSER = "composer"
    LYRICIST = "lyricist"
    WRITER = "writer"
    TRANSLATOR = "translator"
    ADAPTER = "adapter"
    ARRANGER = "arranger"
    OTHER = "other"


class WorkRelationType(StrEnum):
    TRANSLATION_OF = "translation_of"
    ADAPTATION_OF = "adaptation_of"
    ARRANGEMENT_OF = "arrangement_of"
    MEDLEY_OF = "medley_of"


class LyricsUsageKind(StrEnum):
    PERFORMABLE = "performable"
    READING_TRANSLATION = "reading_translation"


class LyricsCreationMethod(StrEnum):
    ORIGINAL = "original"
    HUMAN_TRANSLATION = "human_translation"
    MACHINE_TRANSLATION = "machine_translation"


class LyricsVersionRelationType(StrEnum):
    TRANSLATION_OF = "translation_of"
    ADAPTATION_OF = "adaptation_of"


class RecordingCreditTargetKind(StrEnum):
    PERSON = "person"
    GROUP = "group"


class BillingRole(StrEnum):
    PRIMARY = "primary"
    FEATURED = "featured"
    ADDITIONAL = "additional"
    UNBILLED = "unbilled"
    UNKNOWN = "unknown"


class RecordingContributionKind(StrEnum):
    VOCAL = "vocal"
    INSTRUMENTAL = "instrumental"
    BANDLEADER = "bandleader"
    CONDUCTOR = "conductor"
    ARRANGER = "arranger"
    COMPOSER = "composer"
    LYRICIST = "lyricist"
    PRODUCER = "producer"
    OTHER = "other"
    UNKNOWN = "unknown"


class RecordingWorkUsageKind(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    MEDLEY_COMPONENT = "medley_component"
