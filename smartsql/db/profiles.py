"""
T-1.02: Named database profile registry.

Profiles are resolved from environment variables for path/DSN overrides,
with sensible defaults for the three bundled SQLite sample databases.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Repository root — two levels up from this file (smartsql/db/profiles.py)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"


class ProfileNotFoundError(KeyError):
    """Raised when an unknown profile ID is requested."""

    def __init__(self, profile_id: str) -> None:
        self.profile_id = profile_id
        super().__init__(
            f"Unknown database profile: {profile_id!r}. "
            f"Valid profiles: {sorted(_REGISTRY.keys())}"
        )


@dataclass(frozen=True)
class DatabaseProfile:
    """Immutable descriptor for a named database connection."""

    profile_id: str
    dialect: Literal["sqlite", "mysql"]
    # For SQLite: file path (str). For MySQL: full DSN from env.
    url: str
    pool_size: int = 1
    connect_timeout: int = 10  # seconds

    @property
    def is_sqlite(self) -> bool:
        return self.dialect == "sqlite"


def _sqlite_url(filename: str, env_var: str) -> str:
    """Return a SQLite URL, preferring an env override."""
    override = os.environ.get(env_var)
    if override:
        return f"sqlite:///{override}"
    return f"sqlite:///{_DATA_DIR / filename}"


def _mysql_url(env_var: str = "MYSQL_DSN") -> str:
    """Return a MySQL DSN from env, or a placeholder (raises at connect time)."""
    return os.environ.get(env_var, "mysql+pymysql://user:pass@localhost/smartsql")


# ---------------------------------------------------------------------------
# Registry — add profiles here; do NOT add a free-form connection-string box.
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, DatabaseProfile] = {
    "university": DatabaseProfile(
        profile_id="university",
        dialect="sqlite",
        url=_sqlite_url("university.db", "SMARTSQL_UNIVERSITY_PATH"),
    ),
    "ecommerce": DatabaseProfile(
        profile_id="ecommerce",
        dialect="sqlite",
        url=_sqlite_url("ecommerce.db", "SMARTSQL_ECOMMERCE_PATH"),
    ),
    "hr_analytics": DatabaseProfile(
        profile_id="hr_analytics",
        dialect="sqlite",
        url=_sqlite_url("hr_analytics.db", "SMARTSQL_HR_PATH"),
    ),
    # MySQL optional — only available if MYSQL_DSN is set in the environment.
    "mysql_optional": DatabaseProfile(
        profile_id="mysql_optional",
        dialect="mysql",
        url=_mysql_url(),
        pool_size=5,
    ),
}


def get_profile(profile_id: str) -> DatabaseProfile:
    """Return the named :class:`DatabaseProfile`.

    Raises
    ------
    ProfileNotFoundError
        If *profile_id* is not registered.
    """
    try:
        return _REGISTRY[profile_id]
    except KeyError:
        raise ProfileNotFoundError(profile_id)


def list_profiles() -> list[str]:
    """Return all registered profile IDs (sorted)."""
    return sorted(_REGISTRY.keys())
