from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.repositories.project_repository import ProjectRepository
from app.services.project_service import ProjectService

security = HTTPBearer()


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(session)

async def get_project_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> ProjectRepository:
    return ProjectRepository(session)


async def get_project_service(
    repository: Annotated[
        ProjectRepository,
        Depends(get_project_repository),
    ],
) -> ProjectService:
    return ProjectService(repository)

async def get_user_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> UserService:
    return UserService(repository)


async def get_auth_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> AuthService:
    return AuthService(repository)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    token = credentials.credentials

    user_id = await get_current_user_id(token)

    user = await user_service.get_user(user_id)

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    if not current_user.is_active:
        raise UnauthorizedException(
            "Inactive user."
        )

    return current_user