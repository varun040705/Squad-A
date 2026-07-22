"""
User ORM model.

This module defines the application's authentication user model using
SQLAlchemy 2.0 typed ORM mappings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID as PyUUID
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db.base import Base
from sqlalchemy import text


class UserRole(str, Enum):
    """
    Application user roles.
    """

    ADMIN = "admin"
    USER = "user"


class User(Base):
    """
    Authentication user entity.
    """

    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(
    PGUUID(as_uuid=True),
    primary_key=True,
    default=uuid4,
)

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role",
        ),
        default=UserRole.USER,
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
    Boolean,
    default=True,
    server_default=text("true"),
    nullable=False,
)

    is_verified: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    server_default=text("false"),
    nullable=False,
)

    is_superuser: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    server_default=text("false"),
    nullable=False,
)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    __table_args__ = {
        "comment": "Stores application users for authentication and authorization.",
    }

    @property
    def full_name(self) -> str:
        """
        Returns the user's full name.
        """
        return f"{self.first_name} {self.last_name}".strip()

    def activate(self) -> None:
        """
        Activate the user account.
        """
        self.is_active = True

    def deactivate(self) -> None:
        """
        Deactivate the user account.
        """
        self.is_active = False

    def verify(self) -> None:
        """
        Mark the user account as verified.
        """
        self.is_verified = True

    def promote_to_admin(self) -> None:
        """
        Promote the user to an administrator.
        """
        self.role = UserRole.ADMIN
        self.is_superuser = True

    def demote_to_user(self) -> None:
        """
        Remove administrator privileges.
        """
        self.role = UserRole.USER
        self.is_superuser = False

    def record_login(self) -> None:
        """
        Update the last successful login timestamp.
        """
        self.last_login_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """
        return (
            f"User("
            f"id={self.id!r}, "
            f"username={self.username!r}, "
            f"email={self.email!r}, "
            f"role={self.role.value!r}"
            f")"
        )
    @property
    def is_admin(self) -> bool:
        """
        Returns True if the user has administrator privileges.
        """
        return self.role is UserRole.ADMIN

    @property
    def display_name(self) -> str:
        """
        Preferred display name.
        """
        return self.full_name if self.full_name.strip() else self.username