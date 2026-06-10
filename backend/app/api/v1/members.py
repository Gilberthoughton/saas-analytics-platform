"""Organization member management (RBAC: admin or higher)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AuthContext, CurrentContext, DbSession, require_role
from app.core.rbac import Role
from app.schemas.organization import MemberInvite, MemberRead, RoleUpdate
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/members", tags=["members"])

RequireAdmin = Depends(require_role(Role.admin))


@router.get("", response_model=list[MemberRead], summary="List organization members")
def list_members(context: CurrentContext, db: DbSession) -> list[MemberRead]:
    return OrganizationService(db).list_members(context.organization_id)


@router.post(
    "",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an existing user to the organization",
)
def add_member(
    payload: MemberInvite,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> MemberRead:
    try:
        member = OrganizationService(db).add_member(
            org_id=context.organization_id,
            email=payload.email,
            role=payload.role,
            actor_user_id=context.user.id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization.",
        ) from None
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user with that email exists.",
        )
    return member


@router.patch(
    "/{user_id}",
    response_model=MemberRead,
    summary="Update a member's role",
)
def update_member_role(
    user_id: UUID,
    payload: RoleUpdate,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> MemberRead:
    member = OrganizationService(db).update_role(
        org_id=context.organization_id,
        target_user_id=user_id,
        role=payload.role,
        actor_user_id=context.user.id,
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found."
        )
    return member
