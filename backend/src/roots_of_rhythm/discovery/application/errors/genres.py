class GenreOverviewNotFound(Exception):
    """Published Genre overview is absent or not publicly visible."""


class GenreOverviewAssemblyError(Exception):
    """Published Genre exists but cannot be safely projected to the public overview."""


class GenreRelationsNotFound(Exception):
    """Published Genre relations are absent because the Genre is not publicly visible."""


class GenreRelationsAssemblyError(Exception):
    """Published Genre exists but relations cannot be safely projected."""


class GenreSourcesNotFound(Exception):
    """Published Genre sources are absent because the Genre is not publicly visible."""


class GenreSourcesAssemblyError(Exception):
    """Published Genre exists but sources cannot be safely projected."""
