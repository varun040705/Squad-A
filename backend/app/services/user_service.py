"""
User service.

Contains business logic related to users.
"""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    User business logic.
    """

    def __init__(
        self,
        repository: UserRepository,
    ) -> None:
        self._repository = repository

    async def create_user(
        self,
        user_in: UserCreate,
    ) -> User:
        """
        Create a new user.
        """

        if await self._repository.exists_by_email(user_in.email):
            raise ConflictException(
                "Email already registered."
            )

        if await self._repository.exists_by_username(user_in.username):
            raise ConflictException(
                "Username already exists."
            )

        user = User(
            email=user_in.email,
            username=user_in.username,
            password_hash=hash_password(user_in.password),
            first_name=user_in.first_name,
            last_name=user_in.last_name,
        )

        return await self._repository.create(
            user=user,
        )

    async def get_user(
        self,
        user_id: UUID,
    ) -> User:
        """
        Retrieve a user by ID.
        """

        user = await self._repository.get_by_id(
            user_id,
        )

        if user is None:
            raise ResourceNotFoundException(
                "User not found."
            )

        return user

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email.
        """

        return await self._repository.get_by_email(
            email,
        )

    async def get_user_by_username(
        self,
        username: str,
    ) -> User | None:
        """
        Retrieve a user by username.
        """

        return await self._repository.get_by_username(
            username,
        )

    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Return all users.
        """

        return await self._repository.list(
            skip=skip,
            limit=limit,
        )

    async def update_user(
        self,
        *,
        user_id: UUID,
        user_in: UserUpdate,
    ) -> User:
        """
        Update a user.
        """

        db_user = await self.get_user(
            user_id,
        )

        if (
            user_in.email
            and user_in.email.lower() != db_user.email.lower()
        ):
            if await self._repository.exists_by_email(
                user_in.email,
            ):
                raise ConflictException(
                    "Email already registered."
                )

        if (
            user_in.username
            and user_in.username.lower() != db_user.username.lower()
        ):
            if await self._repository.exists_by_username(
                user_in.username,
            ):
                raise ConflictException(
                    "Username already exists."
                )

        return await self._repository.update(
            db_user=db_user,
            user_in=user_in,
        )

    async def delete_user(
        self,
        user_id: UUID,
    ) -> None:
        """
        Delete a user.
        """

        db_user = await self.get_user(
            user_id,
        )

        await self._repository.delete(
            db_user=db_user,
        )

    async def activate_user(
        self,
        user_id: UUID,
    ) -> User:
        """
        Activate a user.
        """

        user = await self.get_user(
            user_id,
        )

        user.activate()

        return await self._repository.save(
            db_user=user,
        )

    async def deactivate_user(
        self,
        user_id: UUID,
    ) -> User:
        """
        Deactivate a user.
        """

        user = await self.get_user(
            user_id,
        )

        user.deactivate()

        return await self._repository.save(
            db_user=user,
        )

    async def verify_user(
        self,
        user_id: UUID,
    ) -> User:
        """
        Mark a user as verified.
        """

        user = await self.get_user(
            user_id,
        )

        user.verify()

        return await self._repository.save(
            db_user=user,
        )

    async def promote_to_admin(
        self,
        user_id: UUID,
    ) -> User:
        """
        Promote a user to administrator.
        """

        user = await self.get_user(
            user_id,
        )

        user.promote_to_admin()

        return await self._repository.save(
            db_user=user,
        )

    async def demote_to_user(
        self,
        user_id: UUID,
    ) -> User:
        """
        Demote an administrator.
        """

        user = await self.get_user(
            user_id,
        )

        user.demote_to_user()

        return await self._repository.save(
            db_user=user,
        )