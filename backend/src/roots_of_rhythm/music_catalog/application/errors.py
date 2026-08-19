class GenreNotFound(LookupError):
    pass


class GenreNameConflict(ValueError):
    pass


class UniqueConstraintViolation(Exception):
    """Infrastructure uniqueness failure surfaced by Unit of Work adapters.

    Application services map this to domain-facing conflicts (e.g. GenreNameConflict).
    """

    def __init__(self, constraint_name: str | None = None) -> None:
        self.constraint_name = constraint_name
        super().__init__(constraint_name or "unique constraint violated")


class ClassificationAssignmentNotFound(LookupError):
    pass


class ClassificationAssignmentConflict(ValueError):
    pass


class ClassificationAssignmentPersonNotPublished(ValueError):
    pass


class ClassificationAssignmentGenreNotPublished(ValueError):
    pass


class ClassificationAssignmentTargetUnsupported(ValueError):
    pass
