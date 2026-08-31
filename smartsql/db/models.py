"""
T-1.04: Canonical schema snapshot data models.

These dataclasses are the internal representation produced by
:mod:`smartsql.db.inspector` and consumed by serializers, the sampler,
and all downstream prompt builders.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnInfo:
    """Metadata for a single table column."""

    name: str
    sql_type: str          # e.g. "VARCHAR(255)", "INTEGER", "REAL"
    nullable: bool = True
    default: Any = None    # raw default value or None
    comment: str = ""      # populated by inspector or sidecar
    # Populated by T-1.06 sampler when cardinality is below threshold
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class PrimaryKeyInfo:
    """Primary key descriptor for a table."""

    columns: list[str]


@dataclass
class ForeignKeyEdge:
    """Directed FK edge from a referencing column to a referenced column."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str


@dataclass
class TableInfo:
    """Metadata for a single table."""

    name: str
    comment: str = ""
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_key: PrimaryKeyInfo = field(default_factory=lambda: PrimaryKeyInfo(columns=[]))
    foreign_keys: list[ForeignKeyEdge] = field(default_factory=list)

    def column(self, name: str) -> ColumnInfo | None:
        """Return the column with *name*, or ``None``."""
        return next((c for c in self.columns if c.name == name), None)


@dataclass
class SchemaSnapshot:
    """Full schema representation for one database profile."""

    profile_id: str
    dialect: str          # "sqlite" | "mysql"
    tables: list[TableInfo] = field(default_factory=list)
    # Undirected join-path list derived from all FK edges
    join_paths: list[ForeignKeyEdge] = field(default_factory=list)
    # Set by T-1.07 hashing module
    schema_hash: str = ""

    def table(self, name: str) -> TableInfo | None:
        """Return the table with *name*, or ``None``."""
        return next((t for t in self.tables if t.name == name), None)

    @property
    def table_names(self) -> list[str]:
        return [t.name for t in self.tables]
