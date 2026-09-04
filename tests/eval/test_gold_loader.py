"""
Tests for T-1.11: gold file loader.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from smartsql.eval.gold import GoldItem, GoldLoadError, load_gold


@pytest.fixture
def gold_dir(tmp_path) -> Path:
    """Write a minimal 3-item gold YAML fixture."""
    yaml_content = textwrap.dedent("""\
        - id: test_001
          question: "How many rows?"
          gold_sql: "SELECT COUNT(*) FROM t"
          required_tables: [t]
          tags: [aggregate]
          expected_row_count: 1

        - id: test_002
          question: "List all items."
          gold_sql: "SELECT * FROM t"
          required_tables: [t]
          tags: [filter]

        - id: test_003
          question: "Average value."
          gold_sql: "SELECT AVG(val) FROM t"
          required_tables: [t]
          tags: [aggregate]
    """)
    (tmp_path / "fixture.yaml").write_text(yaml_content, encoding="utf-8")
    return tmp_path


def test_load_gold_returns_list(gold_dir):
    items = load_gold("fixture", gold_dir=gold_dir)
    assert isinstance(items, list)
    assert len(items) == 3


def test_load_gold_item_fields(gold_dir):
    items = load_gold("fixture", gold_dir=gold_dir)
    item = items[0]
    assert item.id == "test_001"
    assert "COUNT" in item.gold_sql
    assert item.required_tables == ["t"]
    assert "aggregate" in item.tags
    assert item.expected_row_count == 1


def test_load_gold_optional_row_count(gold_dir):
    items = load_gold("fixture", gold_dir=gold_dir)
    assert items[1].expected_row_count is None


def test_load_gold_missing_file_raises(tmp_path):
    with pytest.raises(GoldLoadError):
        load_gold("nonexistent", gold_dir=tmp_path)


def test_load_gold_missing_key_raises(tmp_path):
    bad = textwrap.dedent("""\
        - id: bad_001
          question: "Missing required fields"
    """)
    (tmp_path / "bad.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(GoldLoadError):
        load_gold("bad", gold_dir=tmp_path)


def test_load_gold_empty_sql_raises(tmp_path):
    bad = textwrap.dedent("""\
        - id: bad_002
          question: "Empty SQL"
          gold_sql: "   "
          required_tables: [t]
          tags: [filter]
    """)
    (tmp_path / "bad2.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(GoldLoadError):
        load_gold("bad2", gold_dir=tmp_path)


def test_load_gold_non_list_raises(tmp_path):
    bad = "key: value\n"
    (tmp_path / "bad3.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(GoldLoadError):
        load_gold("bad3", gold_dir=tmp_path)
