"""Health check route."""
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"ok": True, "version": settings.app_version, "db": "ok"}
