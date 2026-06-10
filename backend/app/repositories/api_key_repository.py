"""Data access for API keys (always scoped to an organization)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        self.db.flush()
        return api_key

    def get_for_org(self, org_id: UUID, key_id: UUID) -> ApiKey | None:
        return self.db.scalar(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == org_id)
        )

    def get_by_hash(self, hashed_key: str) -> ApiKey | None:
        return self.db.scalar(select(ApiKey).where(ApiKey.hashed_key == hashed_key))

    def list_for_org(self, org_id: UUID) -> list[ApiKey]:
        return list(
            self.db.scalars(
                select(ApiKey)
                .where(ApiKey.organization_id == org_id)
                .order_by(ApiKey.created_at.desc())
            ).all()
        )
