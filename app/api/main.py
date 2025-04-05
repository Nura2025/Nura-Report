from fastapi import APIRouter

from app.api.routes import auth , patient
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/login", tags=["login"])
