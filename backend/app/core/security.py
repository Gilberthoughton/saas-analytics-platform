"""Security primitives: password + API-key hashing and JWT handling."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Passwords --------------------------------------------------------------


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- JWT --------------------------------------------------------------------


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None


# --- API keys ---------------------------------------------------------------

API_KEY_PREFIX = "sk_live_"


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, hashed_key).

    The full key is shown to the user exactly once; only the hash is stored.
    A non-secret prefix is persisted so keys can be identified in the UI.
    """
    secret = secrets.token_urlsafe(32)
    full_key = f"{API_KEY_PREFIX}{secret}"
    prefix = full_key[: len(API_KEY_PREFIX) + 6]
    return full_key, prefix, hash_api_key(full_key)


def hash_api_key(full_key: str) -> str:
    """Deterministic SHA-256 hash for constant-time lookup by key.

    API keys are high-entropy random tokens (unlike user passwords), so a fast
    deterministic hash is appropriate and lets us look a key up directly.
    """
    return hashlib.sha256(full_key.encode()).hexdigest()
