"""Data access for audit logs."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_for_org(
        self, org_id: UUID, *, action: str | None = None, limit: int = 100
    ) -> list[AuditLog]:
        conditions = [AuditLog.organization_id == org_id]
        if action:
            conditions.append(AuditLog.action == action)
        return list(
            self.db.scalars(
                select(AuditLog)
                .where(*conditions)
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            ).all()
        )
