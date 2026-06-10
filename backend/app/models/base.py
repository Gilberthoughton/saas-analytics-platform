"""Shared model mixins."""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import GUID, new_uuid


class PkMixin:
    """UUID primary key."""

    id: Mapped[GUID] = mapped_column(GUID(), primary_key=True, default=new_uuid)


class TimestampMixin:
    """`created_at` set on insert (UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
