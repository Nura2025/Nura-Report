from fastapi import APIRouter

from app.api.routes import analytics, auth , patient
api_router = APIRouter()

api_router.include_router(auth.router, prefix="/login", tags=["login"])
api_router.include_router(auth.router, prefix="/session", tags=["session"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


