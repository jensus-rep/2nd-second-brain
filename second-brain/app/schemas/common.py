"""Shared response envelope schemas."""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class OkResponse(BaseModel, Generic[T]):
    ok: bool = True
    data: T


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail


def ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def err(code: str, message: str, details: Optional[dict] = None) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, "details": details}}
