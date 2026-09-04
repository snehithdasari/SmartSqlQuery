"""
Tests for T-1.05: schema comments sidecar.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from smartsql.db.comments import load_comments, merge_comments
from smartsql.db.inspector import inspect_schema


@pytest.fixture
def simple_engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE students (student_id INTEGER PRIMARY KEY, name TEXT)"))
        conn.commit()
    return engine


@pytest.fixture
def comments_dir(tmp_path) -> Path:
    """Write a fixture YAML sidecar."""
    yaml_content = textwrap.dedent("""\
        students:
          _comment: "Enrolled students."
          student_id: "Surrogate primary key."
          name: "Full name of the student."
    """)
    (tmp_path / "fixture.yaml").write_text(yaml_content, encoding="utf-8")
    return tmp_path


def test_load_comments_returns_dict(comments_dir):
    comments = load_comments("fixture", comments_dir=comments_dir)
    assert isinstance(comments, dict)
    assert "students" in comments


def test_load_comments_missing_file_returns_empty(tmp_path):
    comments = load_comments("does_not_exist", comments_dir=tmp_path)
    assert comments == {}


def test_merge_comments_table_comment(simple_engine, comments_dir):
    snapshot = inspect_schema(simple_engine, "fixture")
    comments = load_comments("fixture", comments_dir=comments_dir)
    updated = merge_comments(snapshot, comments)
    students = updated.table("students")
    assert students.comment == "Enrolled students."


def test_merge_comments_column_comment(simple_engine, comments_dir):
    snapshot = inspect_schema(simple_engine, "fixture")
    comments = load_comments("fixture", comments_dir=comments_dir)
    updated = merge_comments(snapshot, comments)
    students = updated.table("students")
    name_col = students.column("name")
    assert name_col.comment == "Full name of the student."


def test_merge_comments_does_not_mutate_original(simple_engine, comments_dir):
    snapshot = inspect_schema(simple_engine, "fixture")
    comments = load_comments("fixture", comments_dir=comments_dir)
    original_comment = snapshot.table("students").comment
    merge_comments(snapshot, comments)
    # original snapshot should be unchanged
    assert snapshot.table("students").comment == original_comment


def test_merge_empty_comments_is_noop(simple_engine):
    snapshot = inspect_schema(simple_engine, "fixture")
    updated = merge_comments(snapshot, {})
    assert updated is snapshot  # same object returned when nothing to merge
