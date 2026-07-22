from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from app.api.routes import auth_router
from app.api.routes.auth import router as auth_router
from app.api.routes.project import router as project_router
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.constants import (
    API_DOCS_URL,
    API_REDOC_URL,
    APP_VERSION,
    HEALTH_ENDPOINT,
    OPENAPI_URL,
)
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis, ping_redis

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.

    Initializes external resources on startup and gracefully
    releases them on shutdown.
    """
    logger.info(
        "Application starting",
        app_name=settings.app_name,
    )

    try:
        await ping_redis()

        logger.info(
            "Redis connection established.",
        )

        

    except Exception:
        logger.warning(
            "Redis unavailable. Starting without Redis."
        )
        yield

    finally:
        logger.info(
            "Application shutting down",
            app_name=settings.app_name,
        )

        await close_redis()


app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    debug=settings.debug,
    docs_url=API_DOCS_URL,
    redoc_url=API_REDOC_URL,
    openapi_url=OPENAPI_URL,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    project_router,
    prefix=settings.api_v1_prefix,
)

@app.get(
    HEALTH_ENDPOINT,
    tags=["Health"],
    summary="Health Check",
)
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "application": settings.app_name,
            "environment": settings.app_env,
            "version": APP_VERSION,
        },
    )


@app.get(
    "/",
    include_in_schema=False,
)
async def root() -> JSONResponse:
    """
    Root endpoint.
    """
    return JSONResponse(
        content={
            "message": f"{settings.app_name} is running.",
            "docs": API_DOCS_URL,
            "health": HEALTH_ENDPOINT,
        }
    )