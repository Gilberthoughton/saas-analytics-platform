"""Audit log access (RBAC: admin or higher)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AuthContext, DbSession, require_role
from app.core.rbac import Role
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit"])

RequireAdmin = Depends(require_role(Role.admin))


@router.get("", response_model=list[AuditLogRead], summary="List audit log entries")
def list_audit_logs(
    db: DbSession,
    action: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    context: AuthContext = RequireAdmin,
) -> list[AuditLogRead]:
    return AuditService(db).list(context.organization_id, action=action, limit=limit)
