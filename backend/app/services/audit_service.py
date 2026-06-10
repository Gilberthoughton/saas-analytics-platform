"""Audit logging service.

Records security-relevant actions. `record` adds the entry and flushes but does
not commit — the calling service owns the transaction boundary so the audit
entry is written atomically with the action it describes.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def record(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        meta: dict | None = None,
    ) -> AuditLog:
        return self.repo.add(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=action,
                meta=meta or {},
            )
        )

    def list(self, org_id: UUID, *, action: str | None = None, limit: int = 100):
        return self.repo.list_for_org(org_id, action=action, limit=limit)
