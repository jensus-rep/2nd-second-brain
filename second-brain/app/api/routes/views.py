"""View and ViewItem API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.api.deps import db_session
from app.schemas.common import ok, err
from app.schemas.view import ViewCreate, ViewUpdate, ViewItemCreate, ViewItemReorderRequest
from app.services import view_service

router = APIRouter(prefix="/api/v1/views")


@router.get("")
def list_views(session: Session = Depends(db_session)) -> dict:
    views = view_service.list_views(session)
    return ok([v.model_dump() for v in views])


@router.post("", status_code=201)
def create_view(body: ViewCreate, session: Session = Depends(db_session)) -> dict:
    view = view_service.create_view(session, body)
    return ok(view.model_dump())


@router.get("/{view_id}")
def get_view(view_id: str, session: Session = Depends(db_session)) -> dict:
    view = view_service.get_view(session, view_id)
    if not view:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"View {view_id!r} not found"))
    return ok(view.model_dump())


@router.patch("/{view_id}")
def update_view(view_id: str, body: ViewUpdate, session: Session = Depends(db_session)) -> dict:
    view = view_service.update_view(session, view_id, body)
    if not view:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"View {view_id!r} not found"))
    return ok(view.model_dump())


@router.delete("/{view_id}", status_code=204)
def delete_view(view_id: str, session: Session = Depends(db_session)) -> None:
    deleted = view_service.delete_view(session, view_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"View {view_id!r} not found"))


@router.post("/{view_id}/items", status_code=201)
def add_view_item(view_id: str, body: ViewItemCreate, session: Session = Depends(db_session)) -> dict:
    item, error = view_service.add_view_item(session, view_id, body)
    if error:
        raise HTTPException(status_code=422, detail=err("INVALID_REFERENCE", error))
    return ok(item.model_dump())


@router.delete("/{view_id}/items/{view_item_id}", status_code=204)
def remove_view_item(view_id: str, view_item_id: str, session: Session = Depends(db_session)) -> None:
    deleted = view_service.remove_view_item(session, view_id, view_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"ViewItem {view_item_id!r} not found"))


@router.post("/{view_id}/items/reorder")
def reorder_view_items(
    view_id: str, body: ViewItemReorderRequest, session: Session = Depends(db_session)
) -> dict:
    if not view_service.get_view_model(session, view_id):
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"View {view_id!r} not found"))
    items, error = view_service.reorder_view_items(session, view_id, body.item_ids)
    if error:
        raise HTTPException(status_code=422, detail=err("INVALID_REORDER", error))
    return ok([i.model_dump() for i in items])
