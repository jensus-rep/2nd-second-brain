"""
Update Matrix schemas.
Every operation is explicitly typed.
State and mutation are separate concepts from Snapshot.
"""
from typing import Annotated, Any, Literal, Optional, Union
from pydantic import BaseModel, Field
from app.core.enums import TransactionMode


# ── Operation payloads ────────────────────────────────────────────────────────

class CreateEntryData(BaseModel):
    title: str
    slug: Optional[str] = None
    category: Optional[str] = None
    status: str = "active"
    summary: Optional[str] = None


class UpdateEntryPatch(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None


class AppendBlockData(BaseModel):
    type: str
    content: str = ""
    position: int
    meta: Optional[dict[str, Any]] = None


class InsertBlockData(BaseModel):
    type: str
    content: str = ""
    position: int
    meta: Optional[dict[str, Any]] = None


class UpdateBlockPatch(BaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    position: Optional[int] = None
    meta: Optional[dict[str, Any]] = None


class LinkEntriesData(BaseModel):
    source_entry_id: str
    target_entry_id: str
    relation_type: str
    position: int = 0


class CreateViewData(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "page"
    filter: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None


class UpdateViewPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    filter: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None


class AddViewItemData(BaseModel):
    view_id: str
    entry_id: str
    position: int = 0
    section_label: Optional[str] = None


# ── Typed operation models ────────────────────────────────────────────────────

class OpCreateEntry(BaseModel):
    op: Literal["create_entry"]
    temp_id: Optional[str] = None
    data: CreateEntryData


class OpUpdateEntry(BaseModel):
    op: Literal["update_entry"]
    entry_id: str
    patch: UpdateEntryPatch


class OpDeleteEntry(BaseModel):
    op: Literal["delete_entry"]
    entry_id: str


class OpArchiveEntry(BaseModel):
    op: Literal["archive_entry"]
    entry_id: str


class OpAppendBlock(BaseModel):
    op: Literal["append_block"]
    entry_ref: str  # final entry_id or temp_id
    data: AppendBlockData


class OpInsertBlock(BaseModel):
    op: Literal["insert_block"]
    entry_ref: str
    data: InsertBlockData


class OpUpdateBlock(BaseModel):
    op: Literal["update_block"]
    entry_id: str
    block_id: str
    patch: UpdateBlockPatch


class OpDeleteBlock(BaseModel):
    op: Literal["delete_block"]
    entry_id: str
    block_id: str


class OpReorderBlocks(BaseModel):
    op: Literal["reorder_blocks"]
    entry_id: str
    block_ids: list[str]


class OpLinkEntries(BaseModel):
    op: Literal["link_entries"]
    data: LinkEntriesData


class OpUnlinkRelation(BaseModel):
    op: Literal["unlink_relation"]
    relation_id: str


class OpCreateView(BaseModel):
    op: Literal["create_view"]
    temp_id: Optional[str] = None
    data: CreateViewData


class OpUpdateView(BaseModel):
    op: Literal["update_view"]
    view_id: str
    patch: UpdateViewPatch


class OpDeleteView(BaseModel):
    op: Literal["delete_view"]
    view_id: str


class OpAddViewItem(BaseModel):
    op: Literal["add_view_item"]
    data: AddViewItemData


class OpRemoveViewItem(BaseModel):
    op: Literal["remove_view_item"]
    view_item_id: str


class OpReorderViewItems(BaseModel):
    op: Literal["reorder_view_items"]
    view_id: str
    item_ids: list[str]


# Discriminated union of all operations
AnyOperation = Union[
    OpCreateEntry,
    OpUpdateEntry,
    OpDeleteEntry,
    OpArchiveEntry,
    OpAppendBlock,
    OpInsertBlock,
    OpUpdateBlock,
    OpDeleteBlock,
    OpReorderBlocks,
    OpLinkEntries,
    OpUnlinkRelation,
    OpCreateView,
    OpUpdateView,
    OpDeleteView,
    OpAddViewItem,
    OpRemoveViewItem,
    OpReorderViewItems,
]


# ── Top-level Update Matrix ───────────────────────────────────────────────────

DiscriminatedOperation = Annotated[AnyOperation, Field(discriminator="op")]


class UpdateMatrix(BaseModel):
    schema_version: str = "1.0"
    transaction_id: Optional[str] = None
    mode: TransactionMode = TransactionMode.strict
    operations: list[DiscriminatedOperation] = Field(default=[])


# ── Result schemas ────────────────────────────────────────────────────────────

class OperationResult(BaseModel):
    index: int
    op: str
    status: str
    error: Optional[str] = None


class UpdateMatrixResult(BaseModel):
    transaction_id: Optional[str]
    mode: str
    status: str
    temp_id_map: dict[str, str] = {}
    counts: dict[str, int] = {}
    operations: list[OperationResult] = []
