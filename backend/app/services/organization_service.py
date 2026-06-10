"""Organization membership management (RBAC-governed)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.models.membership import Membership
from app.repositories.organization_repository import (
    MembershipRepository,
    OrganizationRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.organization import MemberRead
from app.services.audit_service import AuditService


class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orgs = OrganizationRepository(db)
        self.memberships = MembershipRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def list_members(self, org_id: UUID) -> list[MemberRead]:
        return [
            MemberRead(user_id=u.id, email=u.email, full_name=u.full_name, role=m.role)
            for m, u in self.memberships.list_for_org(org_id)
        ]

    def add_member(
        self, *, org_id: UUID, email: str, role: Role, actor_user_id: UUID
    ) -> MemberRead | None:
        """Add an existing user by email. Returns None if no such user, raises
        ValueError if already a member."""
        user = self.users.get_by_email(email)
        if user is None:
            return None
        if self.memberships.get(user.id, org_id) is not None:
            raise ValueError("already_member")

        self.memberships.add(
            Membership(user_id=user.id, organization_id=org_id, role=role.value)
        )
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="member.add",
            meta={"email": email, "role": role.value},
        )
        self.db.commit()
        return MemberRead(
            user_id=user.id, email=user.email, full_name=user.full_name, role=role.value
        )

    def update_role(
        self, *, org_id: UUID, target_user_id: UUID, role: Role, actor_user_id: UUID
    ) -> MemberRead | None:
        membership = self.memberships.get(target_user_id, org_id)
        if membership is None:
            return None
        membership.role = role.value
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="member.update_role",
            meta={"user_id": str(target_user_id), "role": role.value},
        )
        self.db.commit()
        user = self.users.get(target_user_id)
        assert user is not None
        return MemberRead(
            user_id=user.id, email=user.email, full_name=user.full_name, role=role.value
        )
