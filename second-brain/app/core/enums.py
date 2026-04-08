"""Domain enumerations."""
from enum import Enum


class EntryStatus(str, Enum):
    active = "active"
    draft = "draft"
    archived = "archived"


class BlockType(str, Enum):
    text = "text"
    markdown = "markdown"
    code = "code"
    list = "list"
    table = "table"
    quote = "quote"


class RelationType(str, Enum):
    related = "related"
    extends = "extends"
    contradicts = "contradicts"
    references = "references"
    duplicate_of = "duplicate_of"


class ViewType(str, Enum):
    page = "page"
    collection = "collection"
    export_profile = "export_profile"


class SourceType(str, Enum):
    manual = "manual"
    import_ = "import"
    agent = "agent"
    llm = "llm"


class UpdateStatus(str, Enum):
    applied = "applied"
    rejected = "rejected"
    partial = "partial"


class TransactionMode(str, Enum):
    strict = "strict"
    best_effort = "best_effort"
