from datetime import datetime  # noqa: TC003 — resolved by SQLAlchemy Mapped on mixin columns

from sqlalchemy import Boolean, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column


class ServiceColumnsMixin:
    """Shared persistence columns. Timestamps are owned by the DB (DEFAULT + UPDATE trigger).

    Application/repos set ``deleted`` on soft-delete only; ordinary saves must not overwrite
    ``created_at`` / ``updated_at`` / ``deleted``.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        default=False,
    )
