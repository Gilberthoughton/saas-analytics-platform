"""Shared FastAPI dependencies: authentication, tenant context, and RBAC.

Two authentication schemes:
- **JWT bearer** for dashboard users (`get_current_user` → `get_auth_context`).
- **API key** (`X-API-Key`) for event ingestion (`get_api_key_context`).

Tenant context: a user may belong to several organizations. The active org is
chosen by the optional `X-Org-Id` header, defaulting to the user's first
membership. RBAC is enforced via `require_role(...)`.
"""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.cache import Cache, get_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.rbac import Role, role_satisfies
from app.core.security import decode_access_token
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.organization_repository import MembershipRepository
from app.repositories.user_repository import UserRepository
from app.services.api_key_service import ApiKeyService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

DbSession = Annotated[Session, Depends(get_db)]
CacheDep = Annotated[Cache, Depends(get_cache)]


@dataclass
class AuthContext:
    """The authenticated user and their active organization + role."""

    user: User
    organization_id: UUID
    role: str


def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exc
    try:
        user = UserRepository(db).get(UUID(subject))
    except ValueError:
        raise credentials_exc from None
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_auth_context(
    db: DbSession,
    user: CurrentUser,
    x_org_id: Annotated[str | None, Header()] = None,
) -> AuthContext:
    memberships = MembershipRepository(db)
    if x_org_id:
        try:
            membership = memberships.get(user.id, UUID(x_org_id))
        except ValueError:
            membership = None
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of the requested organization",
            )
    else:
        membership = memberships.first_for_user(user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no organization",
            )
    return AuthContext(
        user=user, organization_id=membership.organization_id, role=membership.role
    )


CurrentContext = Annotated[AuthContext, Depends(get_auth_context)]


def require_role(minimum: Role):
    """Dependency factory enforcing a minimum role on the active organization."""

    def guard(context: CurrentContext) -> AuthContext:
        if not role_satisfies(context.role, minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum.value}' role or higher",
            )
        return context

    return guard


def get_api_key_context(
    db: DbSession,
    x_api_key: Annotated[str | None, Header()] = None,
) -> ApiKey:
    """Authenticate an ingestion request via the `X-API-Key` header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )
    api_key = ApiKeyService(db).authenticate(x_api_key)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    return api_key


ApiKeyContext = Annotated[ApiKey, Depends(get_api_key_context)]
