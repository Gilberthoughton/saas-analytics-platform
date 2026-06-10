"""API key management (RBAC: admin or higher)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AuthContext, CurrentContext, DbSession, require_role
from app.core.rbac import Role
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyRead
from app.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

RequireAdmin = Depends(require_role(Role.admin))


@router.get("", response_model=list[ApiKeyRead], summary="List API keys")
def list_api_keys(context: CurrentContext, db: DbSession) -> list[ApiKeyRead]:
    return ApiKeyService(db).list(context.organization_id)


@router.post(
    "",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key (plaintext returned once)",
)
def create_api_key(
    payload: ApiKeyCreate,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> ApiKeyCreated:
    api_key, full_key = ApiKeyService(db).create(
        org_id=context.organization_id,
        name=payload.name,
        actor_user_id=context.user.id,
    )
    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        key=full_key,
    )


@router.delete(
    "/{key_id}",
    response_model=ApiKeyRead,
    summary="Revoke an API key",
)
def revoke_api_key(
    key_id: UUID,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> ApiKeyRead:
    api_key = ApiKeyService(db).revoke(
        org_id=context.organization_id, key_id=key_id, actor_user_id=context.user.id
    )
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found."
        )
    return api_key
