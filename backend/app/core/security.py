"""
Security utilities.

Provides:

- Argon2 password hashing
- JWT creation
- JWT decoding
- Common security helpers

Redis-backed token revocation is implemented in Part 2.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_password_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2.
    """
    return _password_hasher.hash(password)

from argon2.exceptions import VerifyMismatchError, InvalidHashError

def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    try:
        result = _password_hasher.verify(password_hash, plain_password)
        print("VERIFY RESULT:", result)
        return result
    except VerifyMismatchError:
        print("VERIFY FAILED: Password does not match")
        return False
    except InvalidHashError as e:
        print("INVALID HASH:", e)
        return False
    except Exception as e:
        print("VERIFY ERROR:", type(e).__name__, e)
        return False

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def utc_now() -> datetime:
    """
    Current UTC time.
    """
    return datetime.now(UTC)


def _expiration_delta(token_type: str) -> timedelta:
    """
    Return expiration duration for a token type.
    """
    if token_type == ACCESS_TOKEN_TYPE:
        return timedelta(
            minutes=settings.access_token_expire_minutes,
        )

    if token_type == REFRESH_TOKEN_TYPE:
        return timedelta(
            days=settings.refresh_token_expire_days,
        )

    raise ValueError(f"Unsupported token type: {token_type}")


def build_token_payload(
    *,
    user: User,
    token_type: str,
) -> dict[str, Any]:
    """
    Build standard JWT claims.
    """
    issued_at = utc_now()
    expires_at = issued_at + _expiration_delta(token_type)

    return {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }


def encode_token(payload: dict[str, Any]) -> str:
    """
    Encode a JWT.
    """
    return jwt.encode(
        payload=payload,
        key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user: User) -> str:
    """
    Create an access token.
    """
    payload = build_token_payload(
        user=user,
        token_type=ACCESS_TOKEN_TYPE,
    )

    return encode_token(payload)


def create_refresh_token(user: User) -> str:
    """
    Create a refresh token.
    """
    payload = build_token_payload(
        user=user,
        token_type=REFRESH_TOKEN_TYPE,
    )

    return encode_token(payload)


def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and verify a JWT signature.

    Raises:
        UnauthorizedException
    """
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if not isinstance(payload, dict):
            raise UnauthorizedException("Invalid token payload.")

        return payload

    except ExpiredSignatureError as exc:
        logger.warning("Expired JWT received.")
        raise UnauthorizedException(
            "Token has expired.",
        ) from exc

    except InvalidTokenError as exc:
        logger.warning("Invalid JWT received.")
        raise UnauthorizedException(
            "Invalid authentication token.",
        ) from exc


def validate_subject(payload: dict[str, Any]) -> UUID:
    """
    Validate and return the subject UUID.
    """
    subject = payload.get("sub")

    if subject is None:
        raise UnauthorizedException(
            "Token subject missing.",
        )

    try:
        return UUID(subject)

    except ValueError as exc:
        raise UnauthorizedException(
            "Invalid token subject.",
        ) from exc


def validate_token_type(
    payload: dict[str, Any],
    expected_type: str,
) -> None:
    """
    Ensure the token type matches the expected value.
    """
    token_type = payload.get("type")

    if token_type != expected_type:
        raise UnauthorizedException(
            "Invalid token type.",
        )


def get_jti(payload: dict[str, Any]) -> str:
    """
    Return the token JTI.
    """
    jti = payload.get("jti")

    if not isinstance(jti, str):
        raise UnauthorizedException(
            "Token identifier missing.",
        )

    return jti
# ---------------------------------------------------------------------------
# Redis Token Denylist
# ---------------------------------------------------------------------------

from redis.exceptions import RedisError

from app.core.redis import redis_client


def _denylist_key(jti: str) -> str:
    """
    Generate the Redis key used for revoked tokens.
    """
    return f"jwt:denylist:{jti}"


async def revoke_token(
    token: str,
) -> None:
    """
    Revoke a JWT by storing its JTI in Redis until the
    original token expiration time.

    Raises:
        UnauthorizedException
    """
    payload = decode_token(token)

    jti = get_jti(payload)

    exp = payload.get("exp")

    if not isinstance(exp, int):
        raise UnauthorizedException(
            "Invalid token expiration.",
        )

    ttl = exp - int(utc_now().timestamp())

    if ttl <= 0:
        return

    try:
        await redis_client.set(
            _denylist_key(jti),
            "revoked",
            ex=ttl,
        )

    except RedisError as exc:
        logger.exception(
            "Failed to revoke JWT.",
        )

        raise UnauthorizedException(
            "Authentication service unavailable.",
        ) from exc


async def is_token_revoked(
    jti: str,
) -> bool:
    """
    Check whether a JWT has been revoked.

    During local development, if Redis is unavailable,
    assume the token has not been revoked.
    """

    try:
        return (
            await redis_client.exists(
                _denylist_key(jti),
            )
            == 1
        )

    except RedisError:
        logger.warning(
        "Redis unavailable. Skipping token denylist check (local development)."
    )

    return False


# ---------------------------------------------------------------------------
# High-Level Validation
# ---------------------------------------------------------------------------


async def verify_token(
    token: str,
    *,
    expected_type: str,
) -> dict[str, Any]:
    """
    Fully validate a JWT.

    Performs:

    • Signature verification
    • Expiration verification
    • Token type verification
    • Subject validation
    • Redis denylist verification

    Returns:
        Decoded JWT payload.
    """
    payload = decode_token(token)

    validate_token_type(
        payload,
        expected_type,
    )

    validate_subject(payload)

    jti = get_jti(payload)

    revoked = await is_token_revoked(jti)

    if revoked:
        raise UnauthorizedException(
            "Token has been revoked.",
        )

    return payload


async def verify_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Validate an access token.
    """
    return await verify_token(
        token,
        expected_type=ACCESS_TOKEN_TYPE,
    )


async def verify_refresh_token(
    token: str,
) -> dict[str, Any]:
    """
    Validate a refresh token.
    """
    return await verify_token(
        token,
        expected_type=REFRESH_TOKEN_TYPE,
    )


# ---------------------------------------------------------------------------
# User Helpers
# ---------------------------------------------------------------------------


async def get_current_user_id(
    token: str,
) -> UUID:
    """
    Extract the authenticated user's UUID from an access token.
    """
    payload = await verify_access_token(
        token,
    )

    return validate_subject(payload)


async def get_current_token_jti(
    token: str,
) -> str:
    """
    Extract the JWT identifier (JTI).
    """
    payload = await verify_access_token(
        token,
    )

    return get_jti(payload)


async def revoke_access_token(
    token: str,
) -> None:
    """
    Revoke an access token.
    """
    await revoke_token(token)


async def revoke_refresh_token(
    token: str,
) -> None:
    """
    Revoke a refresh token.
    """
    await revoke_token(token)