"""API key management + ingestion authentication."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import generate_api_key, hash_api_key
from app.models.api_key import ApiKey
from app.repositories.api_key_repository import ApiKeyRepository
from app.services.audit_service import AuditService


class ApiKeyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ApiKeyRepository(db)
        self.audit = AuditService(db)

    def create(
        self, *, org_id: UUID, name: str, actor_user_id: UUID
    ) -> tuple[ApiKey, str]:
        """Create a key; returns the model and the one-time plaintext key."""
        full_key, prefix, hashed = generate_api_key()
        api_key = self.repo.add(
            ApiKey(organization_id=org_id, name=name, prefix=prefix, hashed_key=hashed)
        )
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="api_key.create",
            meta={"name": name, "prefix": prefix},
        )
        self.db.commit()
        self.db.refresh(api_key)
        return api_key, full_key

    def list(self, org_id: UUID) -> list[ApiKey]:
        return self.repo.list_for_org(org_id)

    def revoke(
        self, *, org_id: UUID, key_id: UUID, actor_user_id: UUID
    ) -> ApiKey | None:
        api_key = self.repo.get_for_org(org_id, key_id)
        if api_key is None or api_key.revoked_at is not None:
            return api_key
        api_key.revoked_at = datetime.now(UTC)
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="api_key.revoke",
            meta={"prefix": api_key.prefix},
        )
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def authenticate(self, full_key: str) -> ApiKey | None:
        """Resolve an active API key from its plaintext value (ingestion auth)."""
        api_key = self.repo.get_by_hash(hash_api_key(full_key))
        if api_key is None or api_key.revoked_at is not None:
            return None
        api_key.last_used_at = datetime.now(UTC)
        self.db.commit()
        return api_key
