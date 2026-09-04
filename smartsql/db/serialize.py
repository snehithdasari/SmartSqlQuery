"""
T-1.07: Snapshot serializers — JSON, DDL, and Markdown.

All three formats are derived from the canonical :class:`SchemaSnapshot`.
Stable key order in the JSON output is required for reproducible hashing.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from smartsql.db.models import ForeignKeyEdge, SchemaSnapshot


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def to_json(snapshot: SchemaSnapshot) -> str:
    """Return a canonical, stable-key-order JSON string of *snapshot*.

    The ``schema_hash`` field is **excluded** from the hash source
    (see :func:`smartsql.db.hashing.compute_hash`) to avoid circularity.
    """
    d = _snapshot_to_dict(snapshot)
    return json.dumps(d, sort_keys=True, ensure_ascii=False, indent=2)


def _snapshot_to_dict(snapshot: SchemaSnapshot) -> dict:
    """Convert snapshot to a plain dict suitable for JSON serialisation."""
    return {
        "profile_id": snapshot.profile_id,
        "dialect": snapshot.dialect,
        "tables": [
            {
                "name": t.name,
                "comment": t.comment,
                "primary_key": {"columns": list(t.primary_key.columns)},
                "columns": [
                    {
                        "name": c.name,
                        "sql_type": c.sql_type,
                        "nullable": c.nullable,
                        "default": c.default,
                        "comment": c.comment,
                        "sample_values": sorted(str(v) for v in c.sample_values),
                    }
                    for c in t.columns
                ],
                "foreign_keys": [
                    {
                        "from_table": fk.from_table,
                        "from_column": fk.from_column,
                        "to_table": fk.to_table,
                        "to_column": fk.to_column,
                    }
                    for fk in t.foreign_keys
                ],
            }
            for t in sorted(snapshot.tables, key=lambda x: x.name)
        ],
    }


# ---------------------------------------------------------------------------
# DDL string (for LLM prompts)
# ---------------------------------------------------------------------------

def to_ddl(snapshot: SchemaSnapshot) -> str:
    """Render a dialect DDL string suitable for inclusion in an LLM prompt.

    Includes:
    * ``CREATE TABLE`` statements with column types.
    * Inline ``--`` comments for tables and columns.
    * ``FOREIGN KEY`` clauses.
    * A ``/* JOIN PATHS */`` section listing FK relationships.
    """
    lines: list[str] = [
        f"-- Dialect: {snapshot.dialect}",
        f"-- Database: {snapshot.profile_id}",
        "",
    ]
    for table in sorted(snapshot.tables, key=lambda t: t.name):
        if table.comment:
            lines.append(f"-- {table.comment}")
        lines.append(f"CREATE TABLE {table.name} (")
        col_lines: list[str] = []
        for col in table.columns:
            null_str = "" if col.nullable else " NOT NULL"
            default_str = f" DEFAULT {col.default}" if col.default is not None else ""
            comment_str = f"  -- {col.comment}" if col.comment else ""
            col_lines.append(f"  {col.name} {col.sql_type}{null_str}{default_str}{comment_str}")
        # FK constraints
        for fk in table.foreign_keys:
            col_lines.append(
                f"  FOREIGN KEY ({fk.from_column}) REFERENCES {fk.to_table}({fk.to_column})"
            )
        lines.append(",\n".join(col_lines))
        lines.append(");")
        # Sample values hint
        for col in table.columns:
            if col.sample_values:
                lines.append(
                    f"-- {table.name}.{col.name} sample values: "
                    + ", ".join(repr(v) for v in col.sample_values[:10])
                )
        lines.append("")

    # Join paths summary
    if snapshot.join_paths:
        lines.append("/* JOIN PATHS")
        for jp in snapshot.join_paths:
            lines.append(f"   {jp.from_table}.{jp.from_column} -> {jp.to_table}.{jp.to_column}")
        lines.append("*/")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown summary (for UI schema explorer)
# ---------------------------------------------------------------------------

def to_markdown(snapshot: SchemaSnapshot) -> str:
    """Render a human-readable Markdown summary of *snapshot*."""
    parts: list[str] = [
        f"# Schema: {snapshot.profile_id}",
        f"**Dialect:** {snapshot.dialect}",
        "",
    ]
    for table in sorted(snapshot.tables, key=lambda t: t.name):
        parts.append(f"## {table.name}")
        if table.comment:
            parts.append(f"*{table.comment}*")
        parts.append("")
        parts.append("| Column | Type | Nullable | Comment |")
        parts.append("|--------|------|----------|---------|")
        for col in table.columns:
            null_str = "Yes" if col.nullable else "No"
            comment_str = col.comment or ""
            parts.append(f"| `{col.name}` | `{col.sql_type}` | {null_str} | {comment_str} |")
        # FK summary
        if table.foreign_keys:
            parts.append("")
            parts.append("**Foreign keys:**")
            for fk in table.foreign_keys:
                parts.append(
                    f"- `{fk.from_column}` → `{fk.to_table}.{fk.to_column}`"
                )
        parts.append("")
    return "\n".join(parts)
