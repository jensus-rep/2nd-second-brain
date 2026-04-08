"""UpdateLog DB model."""
from datetime import datetime
from sqlmodel import Field, SQLModel
from app.core.ids import update_log_id
from app.core.clock import utcnow


class UpdateLog(SQLModel, table=True):
    __tablename__ = "update_logs"

    id: str = Field(default_factory=update_log_id, primary_key=True, max_length=25)
    applied_at: datetime = Field(default_factory=utcnow)
    source_type: str = Field(max_length=20)
    payload_json: str = Field()
    result_json: str = Field()
    status: str = Field(max_length=20)
    created_entities: int = Field(default=0)
    updated_entities: int = Field(default=0)
    deleted_entities: int = Field(default=0)
