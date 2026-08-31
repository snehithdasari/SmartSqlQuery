"""
T-1.06: Low-cardinality value sampler.

For each column in the snapshot, if the number of distinct values is below
*threshold* and the column type looks string/enum-like, store a sample of
distinct values on the :class:`ColumnInfo`.  High-cardinality columns
(emails, UUIDs, free text) and BLOBs are skipped.

Usage
-----
    snapshot = sample_values(engine, snapshot, threshold=50)
"""
from __future__ import annotations

import copy

from sqlalchemy import text
from sqlalchemy.engine import Engine

from smartsql.db.models import SchemaSnapshot

# SQL types that we consider string/enum-like for sampling purposes.
# Comparison is done as a prefix-insensitive substring match on the type string.
_SAMPLEABLE_TYPE_PREFIXES = (
    "varchar", "char", "text", "nvarchar", "nchar", "clob",
    "enum", "set",
    "string",  # SQLAlchemy generic
)

# Types to always skip, even if cardinality is low.
_SKIP_TYPE_PREFIXES = ("blob", "binary", "varbinary", "bytea", "tinyblob", "mediumblob", "longblob")

# Cap on sample list stored per column (to keep the snapshot lean).
_MAX_SAMPLE_VALUES = 20


def _is_sampleable(sql_type: str) -> bool:
    """Return True if *sql_type* is a string/enum-like type worth sampling."""
    t = sql_type.lower()
    for prefix in _SKIP_TYPE_PREFIXES:
        if prefix in t:
            return False
    for prefix in _SAMPLEABLE_TYPE_PREFIXES:
        if t.startswith(prefix) or prefix in t:
            return True
    return False


def sample_values(
    engine: Engine,
    snapshot: SchemaSnapshot,
    threshold: int = 50,
) -> SchemaSnapshot:
    """Return a new snapshot with ``sample_values`` populated on qualifying columns.

    Parameters
    ----------
    engine:
        Connected engine for the profile.
    snapshot:
        Existing :class:`SchemaSnapshot` (not modified; deep-copied).
    threshold:
        Max distinct-value count for a column to be sampled.

    Returns
    -------
    SchemaSnapshot
        Updated snapshot with ``ColumnInfo.sample_values`` set where applicable.
    """
    updated = copy.deepcopy(snapshot)

    with engine.connect() as conn:
        for table in updated.tables:
            for col in table.columns:
                if not _is_sampleable(col.sql_type):
                    continue
                # Check cardinality first (cheap COUNT DISTINCT)
                count_sql = text(
                    f"SELECT COUNT(DISTINCT {col.name}) FROM {table.name}"  # noqa: S608
                )
                try:
                    count_row = conn.execute(count_sql).fetchone()
                    distinct_count = count_row[0] if count_row else 0
                except Exception:
                    continue  # Skip columns that fail (e.g. reserved names)

                if distinct_count == 0 or distinct_count > threshold:
                    continue

                # Fetch sample values
                sample_sql = text(
                    f"SELECT DISTINCT {col.name} FROM {table.name} "  # noqa: S608
                    f"WHERE {col.name} IS NOT NULL LIMIT {_MAX_SAMPLE_VALUES}"
                )
                try:
                    rows = conn.execute(sample_sql).fetchall()
                    col.sample_values = [str(r[0]) for r in rows if r[0] is not None]
                except Exception:
                    col.sample_values = []

    return updated
