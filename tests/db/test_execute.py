"""
Tests for T-1.03: execute_select helper.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from smartsql.db.execute import ExecuteError, execute_select


@pytest.fixture
def mem_engine():
    """In-memory SQLite engine with a small fixture table."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, value REAL)"
        ))
        conn.execute(text(
            "INSERT INTO items VALUES (1,'alpha',10.5),(2,'beta',20.0),(3,'gamma',30.0)"
        ))
        conn.commit()
    return engine


def test_basic_select_returns_dataframe(mem_engine):
    df, meta = execute_select(mem_engine, "SELECT * FROM items ORDER BY id")
    assert list(df.columns) == ["id", "name", "value"]
    assert len(df) == 3
    assert df.iloc[0]["name"] == "alpha"


def test_parameterized_select(mem_engine):
    df, meta = execute_select(
        mem_engine,
        "SELECT * FROM items WHERE value > :min_val",
        params={"min_val": 15.0},
    )
    assert len(df) == 2


def test_elapsed_ms_is_positive(mem_engine):
    _, meta = execute_select(mem_engine, "SELECT * FROM items")
    assert meta["elapsed_ms"] > 0


def test_row_count_in_metadata(mem_engine):
    _, meta = execute_select(mem_engine, "SELECT * FROM items")
    assert meta["row_count"] == 3


def test_truncation(mem_engine):
    df, meta = execute_select(mem_engine, "SELECT * FROM items", max_rows=2)
    assert len(df) == 2
    assert meta["truncated"] is True
    assert meta["row_count"] == 2


def test_no_truncation_when_within_limit(mem_engine):
    _, meta = execute_select(mem_engine, "SELECT * FROM items", max_rows=10)
    assert meta["truncated"] is False


def test_empty_result_returns_empty_df(mem_engine):
    df, meta = execute_select(
        mem_engine,
        "SELECT * FROM items WHERE id = :no_id",
        params={"no_id": 999},
    )
    assert len(df) == 0
    assert meta["row_count"] == 0
    assert meta["truncated"] is False


def test_bad_sql_raises_execute_error(mem_engine):
    with pytest.raises(ExecuteError):
        execute_select(mem_engine, "SELECT nope FROM nowhere")
