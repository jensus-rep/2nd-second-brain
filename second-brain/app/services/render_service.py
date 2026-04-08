"""
Render service — derives display-oriented representations from source content.
Does not own content; only transforms it for reading views.
"""
from typing import Any
from app.schemas.entry import EntryRead
from app.schemas.block import BlockRead


def render_blocks_html(blocks: list[BlockRead]) -> list[dict[str, Any]]:
    """Return a list of rendered block dicts for template use."""
    rendered = []
    for block in sorted(blocks, key=lambda b: b.position):
        rendered.append({
            "id": block.id,
            "type": block.type,
            "content": block.content,
            "position": block.position,
            "meta": block.meta,
            "rendered": _render_block(block),
        })
    return rendered


def _render_block(block: BlockRead) -> str:
    """Produce an HTML snippet for a single block. Templates may use this directly."""
    if block.type == "markdown":
        # Return raw markdown; templates handle display with <pre> or a JS renderer
        return block.content
    if block.type == "text":
        return block.content
    if block.type == "code":
        lang = (block.meta or {}).get("language", "")
        return f"<pre><code class=\"language-{lang}\">{_escape(block.content)}</code></pre>"
    if block.type == "quote":
        return f"<blockquote>{_escape(block.content)}</blockquote>"
    if block.type == "list":
        items = (block.meta or {}).get("items", [])
        li_tags = "".join(f"<li>{_escape(str(item))}</li>" for item in items)
        return f"<ul>{li_tags}</ul>"
    if block.type == "table":
        rows = (block.meta or {}).get("rows", [])
        headers = (block.meta or {}).get("headers", [])
        th = "".join(f"<th>{_escape(str(h))}</th>" for h in headers)
        tr_rows = ""
        for row in rows:
            tds = "".join(f"<td>{_escape(str(cell))}</td>" for cell in row)
            tr_rows += f"<tr>{tds}</tr>"
        return f"<table><thead><tr>{th}</tr></thead><tbody>{tr_rows}</tbody></table>"
    return block.content


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
