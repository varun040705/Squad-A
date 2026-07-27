from fastapi import APIRouter
from app.api.v1.routes import inspection

api_router = APIRouter()
api_router.include_router(inspection.router)
