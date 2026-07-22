# backend/app/schemas/user.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models.user import UserRole


class UserBase(BaseModel):
    """Shared user fields."""

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_names(cls, value: str) -> str:
        return value.strip()


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(char.islower() for char in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        if not any(not char.isalnum() for char in value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_names(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class UserRead(BaseModel):
    """Public user response schema."""

    id: UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: UserRole

    is_active: bool
    is_verified: bool
    is_superuser: bool

    full_name: str
    display_name: str
    is_admin: bool

    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    """Paginated user response."""

    items: list[UserRead]
    total: int


class UserLogin(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request."""

    refresh_token: str


class ChangePassword(BaseModel):
    """Authenticated password change."""

    current_password: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(char.islower() for char in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        if not any(not char.isalnum() for char in value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value


class PasswordResetRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Reset password confirmation."""

    token: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(char.islower() for char in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        if not any(not char.isalnum() for char in value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value