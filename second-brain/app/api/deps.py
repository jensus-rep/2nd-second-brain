"""FastAPI dependency injection."""
from collections.abc import Generator
from fastapi import Depends
from sqlmodel import Session
from app.db.session import get_session


def db_session() -> Generator[Session, None, None]:
    yield from get_session()


SessionDep = Depends(db_session)
