"""Versioned project-data migrations.

``MIGRATIONS[n]`` upgrades a data dict from schema version ``n`` to ``n + 1``.
Old projects must keep opening: add a migration whenever ``ProjectData`` changes
incompatibly, never edit an existing one. Version 1 is the first schema.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.domain.project import CURRENT_SCHEMA_VERSION

Migration = Callable[[dict[str, Any]], dict[str, Any]]

MIGRATIONS: dict[int, Migration] = {}


class SchemaVersionError(ValueError):
    pass


def migrate_to_current(
    data: dict[str, Any],
    *,
    current: int = CURRENT_SCHEMA_VERSION,
    migrations: Mapping[int, Migration] | None = None,
) -> dict[str, Any]:
    migrations = MIGRATIONS if migrations is None else migrations
    version = data.get("schema_version")
    if not isinstance(version, int) or version < 1:
        raise SchemaVersionError("missing or invalid schema_version")
    if version > current:
        raise SchemaVersionError(
            f"project schema_version {version} is newer than supported version {current}"
        )
    out = dict(data)
    while version < current:
        step = migrations.get(version)
        if step is None:
            raise SchemaVersionError(f"no migration from schema_version {version}")
        out = step(out)
        version += 1
        out["schema_version"] = version
    return out
