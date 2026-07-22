from app.api.routes.auth import router as auth_router
from app.api.routes.project import router as project_router

__all__ = [
    "auth_router",
    "project_router",
]