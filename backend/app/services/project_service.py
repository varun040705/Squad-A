"""
Project service.
"""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
)


class ProjectService:
    """
    Project business logic.
    """

    def __init__(
        self,
        repository: ProjectRepository,
    ) -> None:
        self._repository = repository

    async def create_project(
        self,
        *,
        owner_id: UUID,
        project_in: ProjectCreate,
    ) -> Project:
        """
        Create a new project.
        """

        project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=owner_id,
        )

        return await self._repository.create(
            project,
        )

    async def get_project(
        self,
        project_id: UUID,
    ) -> Project:
        """
        Get a project by id.
        """

        project = await self._repository.get_by_id(
            project_id,
        )

        if project is None:
            raise ResourceNotFoundException(
                "Project not found.",
            )

        return project

    async def list_projects(
        self,
    ) -> list[Project]:
        """
        Return all projects.
        """

        return await self._repository.get_all()

    async def list_user_projects(
        self,
        owner_id: UUID,
    ) -> list[Project]:
        """
        Return all projects owned by a user.
        """

        return await self._repository.get_by_owner(
            owner_id,
        )

    async def update_project(
        self,
        project_id: UUID,
        project_in: ProjectUpdate,
    ) -> Project:
        """
        Update a project.
        """

        project = await self.get_project(
            project_id,
        )

        update_data = project_in.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(
                project,
                field,
                value,
            )

        return await self._repository.update(
            project,
        )

    async def delete_project(
        self,
        project_id: UUID,
    ) -> None:
        """
        Delete a project.
        """

        project = await self.get_project(
            project_id,
        )

        await self._repository.delete(
            project,
        )