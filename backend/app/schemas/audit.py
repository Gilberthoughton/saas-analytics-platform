"""Audit log schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    meta: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
