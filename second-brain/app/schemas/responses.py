"""Typed response wrappers used in route return type annotations."""
from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool = True
    version: str
    db: str = "ok"
