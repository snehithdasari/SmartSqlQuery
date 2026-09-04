"""
T-1.11: Gold NL↔SQL evaluation file loader.

Loads ``data/gold/<profile_id>.yaml`` into validated :class:`GoldItem` objects.
Used by tests, the eval harness (Phase 4), and gold-SQL execution checks.

Gold YAML format example
------------------------
    - id: univ_001
      question: "How many students are enrolled in CSE?"
      gold_sql: "SELECT COUNT(*) FROM students WHERE dept_id = 1"
      required_tables: [students]
      tags: [filter, aggregate]
      expected_row_count: 1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from smartsql.paths import GOLD_DIR, REPO_ROOT

_REPO_ROOT = REPO_ROOT
_GOLD_DIR = GOLD_DIR

_REQUIRED_KEYS = {"id", "question", "gold_sql", "required_tables", "tags"}


class GoldLoadError(ValueError):
    """Raised when a gold file has a structural problem."""


@dataclass
class GoldItem:
    """A single NL→SQL evaluation pair."""

    id: str
    question: str
    gold_sql: str
    required_tables: list[str]
    tags: list[str]
    expected_row_count: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.gold_sql.strip():
            raise GoldLoadError(f"Gold item {self.id!r} has an empty gold_sql.")
        if not self.required_tables:
            raise GoldLoadError(f"Gold item {self.id!r} has an empty required_tables list.")


def load_gold(profile_id: str, gold_dir: Path | None = None) -> list[GoldItem]:
    """Load and validate gold items for *profile_id*.

    Parameters
    ----------
    profile_id:
        Matches the filename ``<profile_id>.yaml`` under ``data/gold/``.
    gold_dir:
        Override the default ``data/gold/`` directory (for tests).

    Returns
    -------
    list[GoldItem]
        Validated gold items in file order.

    Raises
    ------
    GoldLoadError
        If the file is missing, any item lacks required keys, or any
        ``gold_sql`` is empty.
    """
    base = gold_dir or _GOLD_DIR
    path = base / f"{profile_id}.yaml"
    if not path.exists():
        raise GoldLoadError(f"Gold file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, list):
        raise GoldLoadError(f"Gold file {path} must be a YAML list at the top level.")

    items: list[GoldItem] = []
    for i, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise GoldLoadError(f"Gold item #{i} in {path} is not a mapping.")
        missing = _REQUIRED_KEYS - entry.keys()
        if missing:
            raise GoldLoadError(
                f"Gold item #{i} (id={entry.get('id', '?')!r}) in {path} "
                f"is missing required keys: {missing}"
            )
        items.append(
            GoldItem(
                id=str(entry["id"]),
                question=str(entry["question"]),
                gold_sql=str(entry["gold_sql"]).strip(),
                required_tables=list(entry["required_tables"]),
                tags=list(entry["tags"]),
                expected_row_count=entry.get("expected_row_count"),
            )
        )
    return items
