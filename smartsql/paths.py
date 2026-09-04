"""Centralized filesystem paths for SmartSQLQuery."""
from __future__ import annotations

from pathlib import Path

# Repository root — smartsql package directory parent
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
COMMENTS_DIR = DATA_DIR / "schema_comments"
SEEDS_DIR = DATA_DIR / "seeds"
