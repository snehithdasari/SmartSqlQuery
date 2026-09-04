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

import copy
import hashlib

from smartsql.db.models import SchemaSnapshot
from smartsql.db.serialize import to_json


def compute_hash(snapshot: SchemaSnapshot) -> SchemaSnapshot:
    """Compute and attach a SHA-256 hash to *snapshot*.

    The hash is derived from the canonical JSON produced by
    :func:`smartsql.db.serialize.to_json`, which excludes the
    ``schema_hash`` field (no circularity).

    The input *snapshot* is **not** modified; a new snapshot with
    ``schema_hash`` filled in is returned (deep-copied).

    Returns
    -------
    SchemaSnapshot
        New snapshot with ``schema_hash`` filled in.
    """
    updated = copy.deepcopy(snapshot)
    canonical = to_json(updated)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    updated.schema_hash = digest
    return updated
