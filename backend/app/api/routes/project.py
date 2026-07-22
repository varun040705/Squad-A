"""
Project API routes.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.api.dependencies.auth import (
    get_current_active_user,
    get_project_service,
)
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)
@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(
        get_current_active_user,
    ),
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> ProjectRead:
    project = await project_service.create_project(
        owner_id=current_user.id,
        project_in=project_in,
    )

    return ProjectRead.model_validate(
        project,
    )
@router.get(
    "",
    response_model=list[ProjectRead],
    summary="List my projects",
)
async def list_projects(
    current_user: User = Depends(
        get_current_active_user,
    ),
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> list[ProjectRead]:
    projects = await project_service.list_user_projects(
        current_user.id,
    )

    return [
        ProjectRead.model_validate(project)
        for project in projects
    ]
@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project",
)
async def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> ProjectRead:
    project = await project_service.get_project(
        project_id,
    )

    return ProjectRead.model_validate(
        project,
    )
@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update project",
)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> ProjectRead:
    project = await project_service.update_project(
        project_id,
        project_in,
    )

    return ProjectRead.model_validate(
        project,
    )
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
)
async def delete_project(
    project_id: UUID,
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> None:
    await project_service.delete_project(
        project_id,
    )
    __all__ = [
    "router",
]