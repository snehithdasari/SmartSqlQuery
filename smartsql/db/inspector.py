"""
T-1.04: Schema inspector — reflects a live engine into a SchemaSnapshot.

Usage
-----
    from smartsql.db.connection import get_engine
    from smartsql.db.inspector import inspect_schema

    engine = get_engine("university")
    snapshot = inspect_schema(engine, profile_id="university")
"""
from __future__ import annotations

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Engine

from smartsql.db.models import (
    ColumnInfo,
    ForeignKeyEdge,
    PrimaryKeyInfo,
    SchemaSnapshot,
    TableInfo,
)


def inspect_schema(engine: Engine, profile_id: str) -> SchemaSnapshot:
    """Reflect the database attached to *engine* into a :class:`SchemaSnapshot`.

    Captures:
    * Tables and their optional comments.
    * Columns: name, SQL type string, nullable, default, comment.
    * Primary keys per table.
    * Foreign keys as :class:`ForeignKeyEdge` objects.
    * Derived undirected join-path list (one entry per FK, both directions
      would be redundant — keep directed for prompt clarity).

    Parameters
    ----------
    engine:
        Connected SQLAlchemy engine.
    profile_id:
        Identifier stored on the snapshot for downstream use.

    Returns
    -------
    SchemaSnapshot
        Populated snapshot; ``schema_hash`` is **not** set here — call
        :func:`smartsql.db.hashing.compute_hash` to fill it.
    """
    dialect_name = engine.dialect.name  # "sqlite" | "mysql" | …
    inspector = sa_inspect(engine)

    tables: list[TableInfo] = []
    all_fk_edges: list[ForeignKeyEdge] = []

    for table_name in inspector.get_table_names():
        # --- table-level comment (SQLite usually returns None) ---
        try:
            tbl_comment = inspector.get_table_comment(table_name).get("text") or ""
        except NotImplementedError:
            tbl_comment = ""

        # --- columns ---
        columns: list[ColumnInfo] = []
        for col in inspector.get_columns(table_name):
            col_type = str(col["type"])
            col_info = ColumnInfo(
                name=col["name"],
                sql_type=col_type,
                nullable=bool(col.get("nullable", True)),
                default=col.get("default"),
                comment=col.get("comment") or "",
            )
            columns.append(col_info)

        # --- primary key ---
        pk_info_raw = inspector.get_pk_constraint(table_name)
        pk = PrimaryKeyInfo(columns=list(pk_info_raw.get("constrained_columns", [])))

        # --- foreign keys ---
        fk_edges: list[ForeignKeyEdge] = []
        for fk in inspector.get_foreign_keys(table_name):
            referred_table = fk.get("referred_table", "")
            local_cols = fk.get("constrained_columns", [])
            referred_cols = fk.get("referred_columns", [])
            for local_col, ref_col in zip(local_cols, referred_cols):
                edge = ForeignKeyEdge(
                    from_table=table_name,
                    from_column=local_col,
                    to_table=referred_table,
                    to_column=ref_col,
                )
                fk_edges.append(edge)
                all_fk_edges.append(edge)

        tbl = TableInfo(
            name=table_name,
            comment=tbl_comment,
            columns=columns,
            primary_key=pk,
            foreign_keys=fk_edges,
        )
        tables.append(tbl)

    return SchemaSnapshot(
        profile_id=profile_id,
        dialect=dialect_name,
        tables=tables,
        join_paths=all_fk_edges,  # directed edges; T-1.07 DDL can note both directions
    )
