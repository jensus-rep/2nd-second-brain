"""JSON serialization helpers for structured meta payloads."""
import json
from typing import Any


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def loads(s: str | None) -> Any:
    if s is None:
        return None
    return json.loads(s)
