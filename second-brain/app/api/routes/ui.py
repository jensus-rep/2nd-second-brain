"""Server-rendered UI routes — Jinja2 + HTMX."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.api.deps import db_session
from app.services import entry_service, view_service, render_service, snapshot_service
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    entries = entry_service.list_entries(session, limit=10)
    views = view_service.list_views(session)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "entries": entries, "views": views},
    )


@router.get("/entries", response_class=HTMLResponse)
def entries_list(
    request: Request,
    status: str | None = None,
    category: str | None = None,
    session: Session = Depends(db_session),
) -> HTMLResponse:
    entries = entry_service.list_entries(session, status=status, category=category, limit=200)
    return templates.TemplateResponse(
        "entries/list.html",
        {"request": request, "entries": entries, "status_filter": status, "category_filter": category},
    )


@router.get("/entries/new", response_class=HTMLResponse)
def entry_new_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("entries/form.html", {"request": request, "entry": None})


@router.get("/entries/{entry_id}", response_class=HTMLResponse)
def entry_detail(request: Request, entry_id: str, session: Session = Depends(db_session)) -> HTMLResponse:
    entry = entry_service.get_entry(session, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    rendered_blocks = render_service.render_blocks_html(entry.blocks)
    return templates.TemplateResponse(
        "entries/detail.html",
        {"request": request, "entry": entry, "rendered_blocks": rendered_blocks},
    )


@router.get("/views", response_class=HTMLResponse)
def views_list(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    views = view_service.list_views(session)
    return templates.TemplateResponse("views/list.html", {"request": request, "views": views})


@router.get("/views/{view_id}", response_class=HTMLResponse)
def view_detail(request: Request, view_id: str, session: Session = Depends(db_session)) -> HTMLResponse:
    view = view_service.get_view(session, view_id)
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    # Enrich items with entry data
    enriched_items = []
    for item in view.items:
        entry = entry_service.get_entry(session, item.entry_id)
        enriched_items.append({"item": item, "entry": entry})
    return templates.TemplateResponse(
        "views/detail.html",
        {"request": request, "view": view, "enriched_items": enriched_items},
    )


@router.get("/imports", response_class=HTMLResponse)
def imports_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("imports/index.html", {"request": request})


@router.get("/exports", response_class=HTMLResponse)
def exports_page(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    snapshot = snapshot_service.export_snapshot(session)
    return templates.TemplateResponse(
        "exports/index.html",
        {"request": request, "snapshot": snapshot},
    )
