"""SQLModel metadata base."""
from sqlmodel import SQLModel

# Re-export for use in alembic env.py
metadata = SQLModel.metadata
