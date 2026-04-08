"""Import/Export API routes."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.api.deps import db_session
from app.schemas.common import ok, err
from app.schemas.update_matrix import UpdateMatrix
from app.services import snapshot_service, update_matrix_service
from app.core.enums import SourceType

router = APIRouter(prefix="/api/v1")


@router.get("/export/snapshot")
def export_snapshot(session: Session = Depends(db_session)) -> dict:
    snapshot = snapshot_service.export_snapshot(session)
    return ok(snapshot.model_dump())


@router.post("/import/snapshot", status_code=200)
def import_snapshot(body: dict[str, Any], session: Session = Depends(db_session)) -> dict:
    try:
        result = snapshot_service.import_snapshot(session, body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=err("IMPORT_ERROR", str(exc)))
    return ok(result.model_dump())


@router.post("/import/update-matrix")
def import_update_matrix(
    body: UpdateMatrix,
    source: str = "agent",
    session: Session = Depends(db_session),
) -> dict:
    # Validate source_type
    valid_sources = {s.value for s in SourceType}
    if source not in valid_sources:
        source = SourceType.agent.value

    result = update_matrix_service.apply_update_matrix(session, body, source_type=source)
    return ok(result.model_dump())
