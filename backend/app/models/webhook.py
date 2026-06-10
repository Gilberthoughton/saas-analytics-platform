"""Webhook subscription + delivery records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.types import GUID
from app.models.base import PkMixin, TimestampMixin

if TYPE_CHECKING:
    pass


class Webhook(PkMixin, TimestampMixin, Base):
    __tablename__ = "webhooks"

    organization_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    # Event names this webhook subscribes to; empty list = all events.
    event_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    deliveries: Mapped[list[WebhookDelivery]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )


class WebhookDelivery(PkMixin, TimestampMixin, Base):
    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    webhook: Mapped[Webhook] = relationship("Webhook", back_populates="deliveries")
