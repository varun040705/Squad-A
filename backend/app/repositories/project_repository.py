"""
Project repository.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    """
    Handles all database operations for Project.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        project: Project,
    ) -> Project:
        self.session.add(project)

        await self.session.commit()

        await self.session.refresh(project)

        return project

    async def get_by_id(
        self,
        project_id: UUID,
    ) -> Project | None:
        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_all(self) -> list[Project]:
        result = await self.session.execute(
            select(Project).order_by(
                Project.created_at.desc(),
            )
        )

        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: UUID,
    ) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(
                Project.owner_id == owner_id,
            )
        )

        return list(result.scalars().all())

    async def update(
        self,
        project: Project,
    ) -> Project:
        await self.session.commit()

        await self.session.refresh(project)

        return project

    async def delete(
        self,
        project: Project,
    ) -> None:
        await self.session.delete(project)

        await self.session.commit()