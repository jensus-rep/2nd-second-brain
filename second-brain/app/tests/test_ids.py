"""Tests for central ID generation utility."""
import pytest
from app.core.ids import (
    entry_id, block_id, relation_id, view_id, view_item_id, update_log_id,
    is_valid_id, _ALPHABET, _ID_LENGTH,
)


def test_entry_id_prefix():
    assert entry_id().startswith("ent_")


def test_block_id_prefix():
    assert block_id().startswith("blk_")


def test_relation_id_prefix():
    assert relation_id().startswith("rel_")


def test_view_id_prefix():
    assert view_id().startswith("view_")


def test_view_item_id_prefix():
    assert view_item_id().startswith("vi_")


def test_update_log_id_prefix():
    assert update_log_id().startswith("ulog_")


def test_id_suffix_length():
    for gen in [entry_id, block_id, relation_id, view_id, view_item_id, update_log_id]:
        eid = gen()
        prefix = eid.split("_", 1)[0] + "_" if "_" in eid else eid
        # Handle "view_" and "vi_" and "ulog_"
        for p in ["ent_", "blk_", "rel_", "view_", "vi_", "ulog_"]:
            if eid.startswith(p):
                suffix = eid[len(p):]
                assert len(suffix) == _ID_LENGTH, f"Bad suffix length for {eid!r}"
                break


def test_suffix_chars_are_alphanumeric():
    eid = entry_id()
    suffix = eid[4:]  # strip "ent_"
    for ch in suffix:
        assert ch in _ALPHABET, f"Non-alphanumeric char {ch!r} in {eid!r}"


def test_ids_are_unique():
    ids = {entry_id() for _ in range(500)}
    assert len(ids) == 500


def test_is_valid_id_true():
    assert is_valid_id(entry_id())
    assert is_valid_id(block_id())
    assert is_valid_id(view_id())


def test_is_valid_id_false():
    assert not is_valid_id("not_an_id")
    assert not is_valid_id("ent_short")
    assert not is_valid_id("")
    assert not is_valid_id("ent_" + "!" * 12)
