"""Audit log — an append-only record of security-relevant actions."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.types import GUID
from app.models.base import PkMixin, TimestampMixin


class AuditLog(PkMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    organization_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    actor_user_id: Mapped[GUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
