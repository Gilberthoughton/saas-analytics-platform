"""Auth routes: register, login, current user."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentContext, DbSession
from app.core.security import create_access_token
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.auth import MeResponse, RegisterRequest, Token, UserRead
from app.services.auth_service import AuthService, EmailAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user and create their organization",
)
def register(payload: RegisterRequest, db: DbSession) -> UserRead:
    try:
        user, _org, _membership = AuthService(db).register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from None
    return user


@router.post("/login", response_model=Token, summary="Obtain a JWT access token")
def login(
    db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = AuthService(db).authenticate(
        email=form_data.username, password=form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=MeResponse, summary="Current user + org context")
def me(context: CurrentContext, db: DbSession) -> MeResponse:
    org = OrganizationRepository(db).get(context.organization_id)
    assert org is not None
    return MeResponse(
        user=UserRead.model_validate(context.user),
        organization_id=org.id,
        organization_name=org.name,
        role=context.role,
    )
