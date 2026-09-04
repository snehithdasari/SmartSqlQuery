"""
T-1.12 / T-1.13: Execute every gold SQL against the matching sample database.

Prerequisites
-------------
Run ``python scripts/seed_all.py`` before this test to generate the .db files.
If a DB file is missing, that test is skipped (not failed) so CI can still run
the rest of Phase 1 without the seeded files.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from smartsql.db.execute import execute_select
from smartsql.eval.gold import load_gold, GoldLoadError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_GOLD_DIR = _DATA_DIR / "gold"

# Map gold profile → DB file
_PROFILES = {
    "university": _DATA_DIR / "university.db",
    "ecommerce":  _DATA_DIR / "ecommerce.db",
    "hr_analytics": _DATA_DIR / "hr_analytics.db",
}


def _gold_params():
    """Build pytest parametrize list: (profile_id, GoldItem)."""
    params = []
    for profile_id, db_path in _PROFILES.items():
        try:
            items = load_gold(profile_id, gold_dir=_GOLD_DIR)
        except GoldLoadError:
            continue
        for item in items:
            params.append(
                pytest.param(
                    profile_id, db_path, item,
                    id=item.id,
                    marks=(
                        pytest.mark.skip(reason=f"{db_path.name} not seeded")
                        if not db_path.exists()
                        else ()
                    ),
                )
            )
    return params


@pytest.mark.parametrize("profile_id,db_path,gold_item", _gold_params())
def test_gold_sql_executes(profile_id: str, db_path: Path, gold_item):
    """Each gold SQL must run without error against the matching database."""
    engine = create_engine(f"sqlite:///{db_path}")
    df, meta = execute_select(engine, gold_item.gold_sql)
    # Gold SQL must return at least a valid (possibly empty) DataFrame
    assert df is not None
    assert meta["elapsed_ms"] >= 0

    # Check expected_row_count when specified
    if gold_item.expected_row_count is not None:
        assert meta["row_count"] == gold_item.expected_row_count, (
            f"{gold_item.id}: expected {gold_item.expected_row_count} rows, "
            f"got {meta['row_count']}"
        )


def test_gold_total_count():
    """Gold set must have 50–80 items across all three profiles."""
    total = 0
    for profile_id in _PROFILES:
        try:
            items = load_gold(profile_id, gold_dir=_GOLD_DIR)
            total += len(items)
        except GoldLoadError:
            pass
    assert 50 <= total <= 80, f"Gold count {total} is outside 50–80 range"
