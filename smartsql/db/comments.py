"""
T-1.05: Schema comments sidecar loader and merger.

SQLite stores no native column/table comments in PRAGMA output.
This module loads human-readable descriptions from
``data/schema_comments/<profile_id>.yaml`` and merges them into an
existing :class:`SchemaSnapshot`.

YAML format example
-------------------
    students:
      _comment: "Enrolled students."
      student_id: "Surrogate primary key."
      name: "Full name of the student."
      gpa: "Grade-point average on a 4.0 scale."

Missing sidecar → empty comments, not a crash.
Missing keys within the sidecar → column comment stays as-is.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from smartsql.db.models import SchemaSnapshot
from smartsql.paths import COMMENTS_DIR, REPO_ROOT

_REPO_ROOT = REPO_ROOT
_COMMENTS_DIR = COMMENTS_DIR
_TABLE_COMMENT_KEY = "_comment"


def load_comments(profile_id: str, comments_dir: Path | None = None) -> dict[str, Any]:
    """Load the comments YAML for *profile_id*.

    Returns an empty dict if the file does not exist (not an error).

    Parameters
    ----------
    profile_id:
        Matches the filename ``<profile_id>.yaml``.
    comments_dir:
        Override the default ``data/schema_comments/`` directory (for tests).

    Returns
    -------
    dict
        Nested dict: ``{table_name: {col_name: "comment", "_comment": "table comment"}}``
    """
    base = comments_dir or _COMMENTS_DIR
    path = base / f"{profile_id}.yaml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def merge_comments(snapshot: SchemaSnapshot, comments: dict[str, Any]) -> SchemaSnapshot:
    """Return a new snapshot with comments applied from *comments*.

    The original *snapshot* is not modified (deep-copied).

    Parameters
    ----------
    snapshot:
        Source snapshot, typically from :func:`smartsql.db.inspector.inspect_schema`.
    comments:
        Output of :func:`load_comments`.

    Returns
    -------
    SchemaSnapshot
        New snapshot with updated ``comment`` fields on tables and columns.
    """
    if not comments:
        return snapshot  # nothing to merge

    updated = copy.deepcopy(snapshot)
    for table in updated.tables:
        tbl_comments = comments.get(table.name)
        if not tbl_comments:
            continue
        # Table-level comment
        if _TABLE_COMMENT_KEY in tbl_comments:
            table.comment = tbl_comments[_TABLE_COMMENT_KEY]
        # Column-level comments
        for col in table.columns:
            if col.name in tbl_comments:
                col.comment = tbl_comments[col.name]
    return updated
