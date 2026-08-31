"""
Tests for T-1.06: low-cardinality value sampler.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from smartsql.db.inspector import inspect_schema
from smartsql.db.sampler import sample_values


@pytest.fixture
def sampler_engine():
    """
    Table with:
      - department (5 distinct string values → should be sampled)
      - email (unique per row → should NOT be sampled at threshold=5)
      - score (REAL — not a string type, should NOT be sampled)
    """
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE employees ("
            "  id INTEGER PRIMARY KEY,"
            "  department TEXT,"
            "  email TEXT UNIQUE,"
            "  score REAL"
            ")"
        ))
        for i, (dept, email, score) in enumerate([
            ("Engineering", "e1@x.com", 4.5),
            ("Sales",       "e2@x.com", 3.2),
            ("HR",          "e3@x.com", 4.0),
            ("Finance",     "e4@x.com", 3.8),
            ("Marketing",   "e5@x.com", 2.9),
        ], start=1):
            conn.execute(text(
                "INSERT INTO employees VALUES (:id, :d, :em, :s)"
            ), {"id": i, "d": dept, "em": email, "s": score})
        conn.commit()
    return engine


def test_low_cardinality_column_is_sampled(sampler_engine):
    snapshot = inspect_schema(sampler_engine, "test")
    snapshot = sample_values(sampler_engine, snapshot, threshold=10)
    emp = snapshot.table("employees")
    dept_col = emp.column("department")
    assert len(dept_col.sample_values) == 5
    assert "Engineering" in dept_col.sample_values


def test_high_cardinality_column_not_sampled(sampler_engine):
    snapshot = inspect_schema(sampler_engine, "test")
    snapshot = sample_values(sampler_engine, snapshot, threshold=3)
    emp = snapshot.table("employees")
    # email has 5 distinct values but threshold is 3 — should NOT be sampled
    email_col = emp.column("email")
    assert len(email_col.sample_values) == 0


def test_non_string_column_not_sampled(sampler_engine):
    snapshot = inspect_schema(sampler_engine, "test")
    snapshot = sample_values(sampler_engine, snapshot, threshold=50)
    emp = snapshot.table("employees")
    score_col = emp.column("score")
    # REAL type should not be sampled
    assert len(score_col.sample_values) == 0


def test_sampler_does_not_mutate_original(sampler_engine):
    snapshot = inspect_schema(sampler_engine, "test")
    dept_before = snapshot.table("employees").column("department").sample_values[:]
    sample_values(sampler_engine, snapshot, threshold=10)
    dept_after = snapshot.table("employees").column("department").sample_values
    assert dept_after == dept_before  # original unchanged
