"""Organization & membership schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.rbac import Role


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MemberRead(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    role: str


class MemberInvite(BaseModel):
    """Add an existing user to the organization by email."""

    email: EmailStr
    role: Role = Role.member


class RoleUpdate(BaseModel):
    role: Role = Field(description="New role for the member")
