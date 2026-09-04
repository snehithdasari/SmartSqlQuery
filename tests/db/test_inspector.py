"""
Tests for T-1.04: schema inspector.

Uses a two-table in-memory SQLite fixture with one FK.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from smartsql.db.inspector import inspect_schema


@pytest.fixture
def two_table_engine():
    """In-memory DB: departments(pk) ← students(fk)."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE departments ("
            "  dept_id INTEGER PRIMARY KEY,"
            "  name TEXT NOT NULL,"
            "  code TEXT NOT NULL UNIQUE"
            ")"
        ))
        conn.execute(text(
            "CREATE TABLE students ("
            "  student_id INTEGER PRIMARY KEY,"
            "  name TEXT NOT NULL,"
            "  dept_id INTEGER NOT NULL,"
            "  gpa REAL DEFAULT 0.0,"
            "  FOREIGN KEY (dept_id) REFERENCES departments(dept_id)"
            ")"
        ))
        conn.commit()
    return engine


def test_inspector_finds_both_tables(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    names = snapshot.table_names
    assert "departments" in names
    assert "students" in names


def test_inspector_dialect(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    assert snapshot.dialect == "sqlite"


def test_inspector_columns(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    dept_table = snapshot.table("departments")
    assert dept_table is not None
    col_names = [c.name for c in dept_table.columns]
    assert "dept_id" in col_names
    assert "name" in col_names
    assert "code" in col_names


def test_inspector_primary_key(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    dept = snapshot.table("departments")
    assert "dept_id" in dept.primary_key.columns


def test_inspector_foreign_key(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    student_table = snapshot.table("students")
    fks = student_table.foreign_keys
    assert len(fks) >= 1
    fk = fks[0]
    assert fk.from_table == "students"
    assert fk.from_column == "dept_id"
    assert fk.to_table == "departments"
    assert fk.to_column == "dept_id"


def test_inspector_join_paths(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    assert len(snapshot.join_paths) >= 1


def test_inspector_profile_id(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "my_profile")
    assert snapshot.profile_id == "my_profile"


def test_inspector_column_types(two_table_engine):
    snapshot = inspect_schema(two_table_engine, "fixture")
    students = snapshot.table("students")
    gpa_col = students.column("gpa")
    assert gpa_col is not None
    # SQLite returns REAL
    assert "REAL" in gpa_col.sql_type.upper() or "FLOAT" in gpa_col.sql_type.upper()
