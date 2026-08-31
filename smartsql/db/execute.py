"""
T-1.03: Parameterized SELECT execution helper.

This is the low-level execute path used by tests and gold-set validation.
It is NOT a safety layer — Phase 2 (safe_execute) wraps it.

Usage
-----
    from sqlalchemy import create_engine
    from smartsql.db.execute import execute_select

    engine = create_engine("sqlite:///data/university.db")
    df, meta = execute_select(engine, "SELECT * FROM students WHERE gpa > :min_gpa",
                              params={"min_gpa": 3.5}, max_rows=100)
    print(meta)  # {"row_count": ..., "elapsed_ms": ..., "truncated": ...}
"""
from __future__ import annotations

import time
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


class ExecuteError(RuntimeError):
    """Raised when a SELECT fails at the database level."""


def execute_select(
    engine: Engine,
    sql: str,
    params: dict[str, Any] | None = None,
    max_rows: int = 1000,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute a SELECT statement and return (DataFrame, metadata).

    Parameters
    ----------
    engine:
        A SQLAlchemy :class:`Engine` (any dialect).
    sql:
        A parameterized SELECT string.  Use ``:name`` placeholders.
    params:
        Bound parameter dict, e.g. ``{"min_gpa": 3.5}``.
    max_rows:
        Client-side row cap.  Fetched rows beyond this limit are dropped.
        The ``truncated`` metadata flag is set when rows are dropped.

    Returns
    -------
    tuple[DataFrame, dict]
        ``(dataframe, {"row_count": int, "elapsed_ms": float, "truncated": bool})``.

    Raises
    ------
    ExecuteError
        On any database-level error (wraps the underlying exception).
    """
    params = params or {}
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            # Fetch one extra row to detect truncation without reading everything
            rows = result.fetchmany(max_rows + 1)
    except Exception as exc:
        raise ExecuteError(f"Query failed: {exc}\nSQL: {sql}") from exc

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    truncated = len(rows) > max_rows
    if truncated:
        rows = rows[:max_rows]

    if rows:
        columns = list(result.keys())
        df = pd.DataFrame(rows, columns=columns)
    else:
        columns = list(result.keys()) if result.returns_rows else []
        df = pd.DataFrame(columns=columns)

    metadata: dict[str, Any] = {
        "row_count": len(df),
        "elapsed_ms": round(elapsed_ms, 3),
        "truncated": truncated,
    }
    return df, metadata
