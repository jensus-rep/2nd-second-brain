"""FastAPI application factory."""
import pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, entries, views, import_export, ui

BASE_DIR = pathlib.Path(__file__).resolve().parent

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Second Brain — structured knowledge system",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# API routes
app.include_router(health.router)
app.include_router(entries.router)
app.include_router(views.router)
app.include_router(import_export.router)

# UI routes (last — catch-all friendly)
app.include_router(ui.router)
