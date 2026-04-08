"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entries",
        sa.Column("id", sa.String(length=20), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_entries_slug", "entries", ["slug"])

    op.create_table(
        "entry_blocks",
        sa.Column("id", sa.String(length=20), primary_key=True),
        sa.Column("entry_id", sa.String(length=20), sa.ForeignKey("entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_entry_blocks_entry_id", "entry_blocks", ["entry_id"])

    op.create_table(
        "relations",
        sa.Column("id", sa.String(length=20), primary_key=True),
        sa.Column("source_entry_id", sa.String(length=20), sa.ForeignKey("entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entry_id", sa.String(length=20), sa.ForeignKey("entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_relations_source_entry_id", "relations", ["source_entry_id"])
    op.create_index("ix_relations_target_entry_id", "relations", ["target_entry_id"])

    op.create_table(
        "views",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("filter_json", sa.Text(), nullable=True),
        sa.Column("sort_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "view_items",
        sa.Column("id", sa.String(length=20), primary_key=True),
        sa.Column("view_id", sa.String(length=25), sa.ForeignKey("views.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_id", sa.String(length=20), sa.ForeignKey("entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_label", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_view_items_view_id", "view_items", ["view_id"])
    op.create_index("ix_view_items_entry_id", "view_items", ["entry_id"])

    op.create_table(
        "update_logs",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_entities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_entities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_entities", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("update_logs")
    op.drop_table("view_items")
    op.drop_table("views")
    op.drop_table("relations")
    op.drop_table("entry_blocks")
    op.drop_table("entries")
