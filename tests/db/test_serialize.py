"""
Tests for T-1.07: snapshot serializers and schema hash.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, text

from smartsql.db.hashing import compute_hash
from smartsql.db.inspector import inspect_schema
from smartsql.db.serialize import to_ddl, to_json, to_markdown


@pytest.fixture
def fk_engine():
    """Two-table engine with FK for DDL test."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE dept (dept_id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(text(
            "CREATE TABLE emp ("
            "  emp_id INTEGER PRIMARY KEY,"
            "  name TEXT,"
            "  dept_id INTEGER,"
            "  FOREIGN KEY (dept_id) REFERENCES dept(dept_id)"
            ")"
        ))
        conn.commit()
    return engine


# ── JSON ─────────────────────────────────────────────────────

def test_to_json_produces_valid_json(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    j = to_json(snapshot)
    data = json.loads(j)
    assert "tables" in data
    assert data["profile_id"] == "test"


def test_to_json_stable_key_order(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    j1 = to_json(snapshot)
    j2 = to_json(snapshot)
    assert j1 == j2


# ── DDL ──────────────────────────────────────────────────────

def test_to_ddl_contains_table_names(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    ddl = to_ddl(snapshot)
    assert "dept" in ddl
    assert "emp" in ddl


def test_to_ddl_contains_fk(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    ddl = to_ddl(snapshot)
    assert "FOREIGN KEY" in ddl
    assert "dept" in ddl


def test_to_ddl_contains_dialect(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    ddl = to_ddl(snapshot)
    assert "sqlite" in ddl.lower()


# ── Markdown ─────────────────────────────────────────────────

def test_to_markdown_contains_table_headings(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    md = to_markdown(snapshot)
    assert "## dept" in md or "## emp" in md


def test_to_markdown_contains_columns(fk_engine):
    snapshot = inspect_schema(fk_engine, "test")
    md = to_markdown(snapshot)
    assert "emp_id" in md
    assert "name" in md


# ── Hash ─────────────────────────────────────────────────────

def test_hash_is_stable(fk_engine):
    s1 = inspect_schema(fk_engine, "test")
    s2 = inspect_schema(fk_engine, "test")
    h1 = compute_hash(s1).schema_hash
    h2 = compute_hash(s2).schema_hash
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_changes_on_schema_change():
    e1 = create_engine("sqlite:///:memory:")
    e2 = create_engine("sqlite:///:memory:")
    with e1.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, x TEXT)"))
        conn.commit()
    with e2.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, x TEXT, y TEXT)"))
        conn.commit()
    s1 = compute_hash(inspect_schema(e1, "test"))
    s2 = compute_hash(inspect_schema(e2, "test"))
    assert s1.schema_hash != s2.schema_hash
