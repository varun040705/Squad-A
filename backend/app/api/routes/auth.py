"""
Authentication API routes.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status

from app.api.dependencies.auth import (
    get_auth_service,
    get_current_active_user,
)
from app.models.user import User
from app.schemas.user import (
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> UserRead:
    """
    Register a new user.
    """

    user = await auth_service.register(
        user_in,
    )

    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> Token:
    """
    Authenticate a user and return JWT tokens.
    """

    tokens = await auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )

    return Token.model_validate(tokens)


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    request: TokenRefresh,
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> Token:
    """
    Generate a new access token using a valid refresh token.
    """

    tokens = await auth_service.refresh(
        request.refresh_token,
    )

    return Token.model_validate(tokens)
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout current user",
)
async def logout(
    request: TokenRefresh,
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> Response:
    """
    Revoke the supplied refresh token.
    """

    await auth_service.logout(
        request.refresh_token,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: User = Depends(
        get_current_active_user,
    ),
) -> UserRead:
    """
    Return the currently authenticated user.
    """

    return UserRead.model_validate(
        current_user,
    )


__all__ = [
    "router",
]