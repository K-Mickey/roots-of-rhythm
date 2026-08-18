class HistoricalKnowledgeDomainError(ValueError):
    pass


class ClaimPublicationError(HistoricalKnowledgeDomainError):
    def __init__(self, missing_fields: tuple[str, ...]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Claim cannot be published; missing: {', '.join(missing_fields)}")
