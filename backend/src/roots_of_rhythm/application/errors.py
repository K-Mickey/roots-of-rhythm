class UniqueConstraintViolation(Exception):
    def __init__(self, constraint_name: str | None = None) -> None:
        self.constraint_name = constraint_name
        super().__init__(constraint_name or "unique constraint violated")
