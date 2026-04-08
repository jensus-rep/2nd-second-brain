"""
Central ID generation utility.
All entity IDs are server-generated with type-prefixed Nano IDs.
Clients and LLMs must not generate final IDs.
"""
import random
import string

# Alphabet: URL-safe alphanumeric only (no hyphens or underscores in the random part)
_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 12


def _generate_suffix() -> str:
    return "".join(random.choices(_ALPHABET, k=_ID_LENGTH))


def entry_id() -> str:
    return f"ent_{_generate_suffix()}"


def block_id() -> str:
    return f"blk_{_generate_suffix()}"


def relation_id() -> str:
    return f"rel_{_generate_suffix()}"


def view_id() -> str:
    return f"view_{_generate_suffix()}"


def view_item_id() -> str:
    return f"vi_{_generate_suffix()}"


def update_log_id() -> str:
    return f"ulog_{_generate_suffix()}"


# Prefix validation helpers
_PREFIX_MAP = {
    "ent_": entry_id,
    "blk_": block_id,
    "rel_": relation_id,
    "view_": view_id,
    "vi_": view_item_id,
    "ulog_": update_log_id,
}

VALID_PREFIXES = tuple(_PREFIX_MAP.keys())


def is_valid_id(value: str) -> bool:
    """Return True if the string matches any known ID prefix pattern."""
    for prefix in VALID_PREFIXES:
        if value.startswith(prefix):
            suffix = value[len(prefix):]
            if len(suffix) == _ID_LENGTH and all(c in _ALPHABET for c in suffix):
                return True
    return False
