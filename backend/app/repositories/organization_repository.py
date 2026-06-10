"""Data access for organizations and memberships."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User


class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, org_id: UUID) -> Organization | None:
        return self.db.get(Organization, org_id)

    def get_by_slug(self, slug: str) -> Organization | None:
        return self.db.scalar(select(Organization).where(Organization.slug == slug))

    def add(self, org: Organization) -> Organization:
        self.db.add(org)
        self.db.flush()
        return org


class MembershipRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.flush()
        return membership

    def get(self, user_id: UUID, org_id: UUID) -> Membership | None:
        return self.db.scalar(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org_id,
            )
        )

    def first_for_user(self, user_id: UUID) -> Membership | None:
        return self.db.scalar(
            select(Membership)
            .where(Membership.user_id == user_id)
            .order_by(Membership.created_at.asc())
        )

    def list_for_org(self, org_id: UUID) -> list[tuple[Membership, User]]:
        rows = self.db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id)
            .order_by(Membership.created_at.asc())
        ).all()
        return [(m, u) for m, u in rows]
