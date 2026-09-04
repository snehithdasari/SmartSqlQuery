"""
Tests for T-1.02: profile registry and connection manager.
"""
from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import text

from smartsql.db.connection import (
    DatabaseConnectionError,
    clear_engine_cache,
    get_engine,
    healthcheck,
)
from smartsql.db.profiles import ProfileNotFoundError, get_profile, list_profiles


# ── Profile registry ──────────────────────────────────────────

def test_known_profiles_exist():
    profiles = list_profiles()
    assert "university" in profiles
    assert "ecommerce" in profiles
    assert "hr_analytics" in profiles


def test_get_profile_returns_dataclass():
    p = get_profile("university")
    assert p.profile_id == "university"
    assert p.dialect == "sqlite"
    assert "university.db" in p.url


def test_unknown_profile_raises():
    with pytest.raises(ProfileNotFoundError):
        get_profile("nonexistent_db")


def test_profile_not_found_error_message():
    with pytest.raises(ProfileNotFoundError) as exc_info:
        get_profile("ghost")
    assert "ghost" in str(exc_info.value)


# ── Engine and healthcheck ────────────────────────────────────

def test_get_engine_on_temp_sqlite(tmp_path):
    """get_engine should return a working engine for a temp SQLite DB."""
    clear_engine_cache()
    db_path = tmp_path / "test.db"
    os.environ["SMARTSQL_UNIVERSITY_PATH"] = str(db_path)
    try:
        engine = get_engine("university")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        del os.environ["SMARTSQL_UNIVERSITY_PATH"]
        clear_engine_cache()


def test_healthcheck_on_temp_sqlite(tmp_path):
    clear_engine_cache()
    db_path = tmp_path / "hc.db"
    os.environ["SMARTSQL_UNIVERSITY_PATH"] = str(db_path)
    try:
        assert healthcheck("university") is True
    finally:
        del os.environ["SMARTSQL_UNIVERSITY_PATH"]
        clear_engine_cache()


def test_healthcheck_missing_profile():
    with pytest.raises(ProfileNotFoundError):
        healthcheck("no_such_profile")


@pytest.mark.mysql
def test_mysql_profile_exists():
    """MySQL profile is registered. Skip if no MYSQL_DSN."""
    p = get_profile("mysql_optional")
    assert p.dialect == "mysql"
