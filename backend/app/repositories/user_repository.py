# backend/app/repositories/user_repository.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """
    Repository layer for User persistence.

    This layer is responsible only for database interaction.
    It must not contain business rules or authentication logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user: User,
    ) -> User:
        """
        Persist a new user.

        The password should already be hashed by the service layer.
        """
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Retrieve a user by primary key.
        """
        statement = select(User).where(User.id == user_id)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email.
        """
        statement = (
            select(User)
            .where(func.lower(User.email) == email.lower())
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        """
        Retrieve a user by username.
        """
        statement = (
            select(User)
            .where(func.lower(User.username) == username.lower())
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:
        """
        Check whether an email already exists.
        """
        statement = (
            select(User.id)
            .where(func.lower(User.email) == email.lower())
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def exists_by_username(
        self,
        username: str,
    ) -> bool:
        """
        Check whether a username already exists.
        """
        statement = (
            select(User.id)
            .where(func.lower(User.username) == username.lower())
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Return a paginated list of users.
        """
        statement = (
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )

        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Return total number of users.
        """
        statement = select(func.count(User.id))

        result = await self._session.execute(statement)

        return int(result.scalar_one())

    async def update(
        self,
        *,
        db_user: User,
        user_in: UserUpdate,
    ) -> User:
        """
        Update an existing user.
        """
        update_data = user_in.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(db_user, field, value)

        await self._s
    async def save(self,
        *,
        db_user: User,
    ) -> User:
        """
        Persist changes to an existing user.
        """
        self._session.add(db_user)
        await self._session.commit()
        await self._session.refresh(db_user)
        return db_user