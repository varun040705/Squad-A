"""
Authentication service.

Contains business logic for:

- Register
- Authenticate
- Login
- Refresh
- Logout
"""

from __future__ import annotations
from uuid import UUID

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_password,
    verify_refresh_token,
)

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    """
    Authentication business logic.
    """

    def __init__(
        self,
        repository: UserRepository,
    ) -> None:
        self._repository = repository

    async def register(
        self,
        user_in: UserCreate,
    ) -> User:
        """
        Register a new user.
        """

        if await self._repository.exists_by_email(
            user_in.email,
        ):
            raise ConflictException(
                "Email already registered.",
            )

        if await self._repository.exists_by_username(
            user_in.username,
        ):
            raise ConflictException(
                "Username already exists.",
            )

        user = User(
            email=user_in.email,
            username=user_in.username,
            password_hash=hash_password(
                user_in.password,
            ),
            first_name=user_in.first_name,
            last_name=user_in.last_name,
        )

        return await self._repository.create(
            user=user,
        )

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> User:
        """
        Authenticate a user.
        """

        user = await self._repository.get_by_email(
            email,
        )

        if user is None:
            raise UnauthorizedException(
                "Invalid email or password.",
            )
        # ================================================================================
        

        result = verify_password(
             password,
        user.password_hash,
        )
        if not result:
            raise UnauthorizedException(
        "Invalid email or password.",
    )
# ================================================================================
        if not user.is_active:
            raise UnauthorizedException(
                "User account is inactive.",
            )

        user.record_login()

        await self._repository.save(
            db_user=user,
        )

        return user

    async def login(
        self,
        *,
        email: str,
        password: str,
    ) -> dict[str, str]:
        """
        Authenticate and issue JWT tokens.
        """

        user = await self.authenticate(
            email=email,
            password=password,
        )

        access_token = create_access_token(
            user,
        )

        refresh_token = create_refresh_token(
            user,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    async def refresh(
        self,
        refresh_token: str,
    ) -> dict[str, str]:
        """
        Validate a refresh token and issue a new token pair.
        """

        payload = await verify_refresh_token(
            refresh_token,
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise UnauthorizedException(
                "Invalid refresh token.",
            )

        user = await self._repository.get_by_id(
    UUID(user_id),
        )
        

        if user is None:
            raise ResourceNotFoundException(
                "User not found.",
            )

        if not user.is_active:
            raise UnauthorizedException(
                "User account is inactive.",
            )

        access_token = create_access_token(
            user,
        )

        new_refresh_token = create_refresh_token(
            user,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        """
        Revoke the supplied refresh token.
        """

        await revoke_refresh_token(
            refresh_token,
        )