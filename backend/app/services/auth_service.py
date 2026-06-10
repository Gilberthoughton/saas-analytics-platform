"""Authentication & registration service."""

from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.core.security import hash_password, verify_password
from app.core.text import slug_with_suffix
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization_repository import (
    MembershipRepository,
    OrganizationRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class EmailAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.orgs = OrganizationRepository(db)
        self.memberships = MembershipRepository(db)
        self.audit = AuditService(db)

    def register(
        self, *, email: str, password: str, full_name: str, organization_name: str
    ) -> tuple[User, Organization, Membership]:
        """Create a user, their organization, and an owner membership atomically."""
        if self.users.get_by_email(email):
            raise EmailAlreadyExistsError()

        user = self.users.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
            )
        )
        org = self.orgs.add(
            Organization(
                name=organization_name, slug=slug_with_suffix(organization_name)
            )
        )
        membership = self.memberships.add(
            Membership(user_id=user.id, organization_id=org.id, role=Role.owner.value)
        )
        self.audit.record(
            organization_id=org.id,
            actor_user_id=user.id,
            action="user.register",
            meta={"email": email},
        )
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(org)
        self.db.refresh(membership)
        return user, org, membership

    def authenticate(self, *, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            return None
        return user
