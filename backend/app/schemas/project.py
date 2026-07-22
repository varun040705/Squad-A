"""
Project Pydantic schemas.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ProjectBase(BaseModel):
    """
    Shared project fields.
    """

    name: str = Field(
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class ProjectCreate(ProjectBase):
    """
    Create project request.
    """

    pass


class ProjectUpdate(BaseModel):
    """
    Update project request.
    """

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    is_active: bool | None = None


class ProjectRead(ProjectBase):
    """
    Project response schema.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    owner_id: UUID

    is_active: bool

    created_at: datetime

    updated_at: datetime


class ProjectList(BaseModel):
    """
    List of projects.
    """

    items: list[ProjectRead]

    total: int