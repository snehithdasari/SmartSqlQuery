"""
T-1.02: SQLAlchemy engine factory and healthcheck.

Usage
-----
    from smartsql.db.connection import get_engine, healthcheck

    engine = get_engine("university")
    ok = healthcheck("university")
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from smartsql.db.profiles import DatabaseProfile, ProfileNotFoundError, get_profile


class DatabaseConnectionError(RuntimeError):
    """Raised when a healthcheck or engine creation fails."""


@lru_cache(maxsize=None)
def _cached_engine(url: str, pool_size: int, connect_timeout: int) -> Engine:
    """Create and cache a SQLAlchemy engine keyed by its URL.

    The cache is intentionally module-level so engines are reused across
    calls within the same process.  Call :func:`clear_engine_cache` in tests
    that need a fresh engine.
    """
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["timeout"] = connect_timeout
    elif url.startswith("mysql"):
        connect_args["connect_timeout"] = connect_timeout

    kwargs: dict = {
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }
    # SQLite doesn't use pool_size
    if not url.startswith("sqlite"):
        kwargs["pool_size"] = pool_size

    return create_engine(url, **kwargs)


def get_engine(profile_id: str) -> Engine:
    """Return a SQLAlchemy :class:`Engine` for the named profile.

    Parameters
    ----------
    profile_id:
        One of the registered profile IDs (e.g. ``"university"``).

    Raises
    ------
    ProfileNotFoundError
        If *profile_id* is not registered.
    DatabaseConnectionError
        If the underlying DB file is missing or the DSN is invalid.
    """
    profile: DatabaseProfile = get_profile(profile_id)
    try:
        return _cached_engine(profile.url, profile.pool_size, profile.connect_timeout)
    except Exception as exc:
        raise DatabaseConnectionError(
            f"Could not create engine for profile {profile_id!r}: {exc}"
        ) from exc


def healthcheck(profile_id: str) -> bool:
    """Run ``SELECT 1`` against the named profile.

    Returns
    -------
    bool
        ``True`` if the DB is reachable.

    Raises
    ------
    ProfileNotFoundError
        If *profile_id* is not registered.
    DatabaseConnectionError
        If the database file is missing or the server is unreachable.
    """
    engine = get_engine(profile_id)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        raise DatabaseConnectionError(
            f"Healthcheck failed for profile {profile_id!r}: {exc}"
        ) from exc


def clear_engine_cache() -> None:
    """Invalidate the engine LRU cache.  Call from tests that swap DB paths."""
    _cached_engine.cache_clear()
