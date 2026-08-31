"""
scripts/seed_all.py — Create all three sample SQLite databases from seed SQL.

Usage (from repo root, inside .venv):
    python scripts/seed_all.py

Re-running is safe: existing DB files are deleted and recreated.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SEEDS_DIR = DATA_DIR / "seeds"

DATABASES = {
    "university":    SEEDS_DIR / "university.sql",
    "ecommerce":     SEEDS_DIR / "ecommerce.sql",
    "hr_analytics":  SEEDS_DIR / "hr_analytics.sql",
}


def seed_database(db_name: str, sql_file: Path) -> None:
    db_path = DATA_DIR / f"{db_name}.db"
    if db_path.exists():
        db_path.unlink()
        print(f"  Removed existing {db_path.name}")

    sql = sql_file.read_text(encoding="utf-8")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(sql)
        conn.commit()
        print(f"  [OK] Created {db_path.name}")
    finally:
        conn.close()


def main() -> None:
    print("Seeding SmartSQLQuery sample databases …")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for db_name, sql_file in DATABASES.items():
        if not sql_file.exists():
            print(f"  ✗ Missing seed file: {sql_file}", file=sys.stderr)
            sys.exit(1)
        print(f"\n[{db_name}]")
        seed_database(db_name, sql_file)
    print("\nDone. All databases ready.")


if __name__ == "__main__":
    main()
