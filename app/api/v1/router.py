"""API v1 Router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, ktp

api_router = APIRouter(prefix="/api/v1")

# Mount endpoints
api_router.include_router(ktp.router)
api_router.include_router(health.router)
