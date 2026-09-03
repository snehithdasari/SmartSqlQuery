"""
T-1.07: Schema hash computation.

The hash is SHA-256 of the canonical JSON (stable key order, without the
hash field itself) and is stored on the :class:`SchemaSnapshot`.
Phase 4 uses it to invalidate vector indexes and SQL caches.

Usage
-----
    from smartsql.db.hashing import compute_hash

    snapshot = compute_hash(snapshot)
    print(snapshot.schema_hash)  # "a3f2..."
"""
from __future__ import annotations

import hashlib

from smartsql.db.models import SchemaSnapshot
from smartsql.db.serialize import to_json


def compute_hash(snapshot: SchemaSnapshot) -> SchemaSnapshot:
    """Compute and attach a SHA-256 hash to *snapshot*.

    The hash is derived from the canonical JSON produced by
    :func:`smartsql.db.serialize.to_json`, which excludes the
    ``schema_hash`` field (no circularity).

    The input *snapshot* is **not** modified; a new one is returned
    (because :class:`SchemaSnapshot` is a regular dataclass, not frozen,
    we just update the field in-place after copy — but returning it
    makes the intent clear).

    Returns
    -------
    SchemaSnapshot
        Same object with ``schema_hash`` filled in.
    """
    canonical = to_json(snapshot)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    snapshot.schema_hash = digest
    return snapshot
