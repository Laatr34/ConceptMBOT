import pytest

from app.infrastructure.migrations import SchemaVersionError, migrate_to_current


def test_current_version_unchanged():
    d = {"schema_version": 1, "info": {"name": "x"}}
    assert migrate_to_current(d) == d


def test_newer_version_rejected():
    with pytest.raises(SchemaVersionError):
        migrate_to_current({"schema_version": 99})


def test_missing_version_rejected():
    with pytest.raises(SchemaVersionError):
        migrate_to_current({"info": {}})


def test_chain_of_migrations_applied_in_order():
    migs = {
        1: lambda d: {**d, "a": 1},
        2: lambda d: {**d, "b": d["a"] + 1},
    }
    out = migrate_to_current({"schema_version": 1}, current=3, migrations=migs)
    assert out == {"schema_version": 3, "a": 1, "b": 2}


def test_missing_migration_step():
    with pytest.raises(SchemaVersionError):
        migrate_to_current({"schema_version": 1}, current=2, migrations={})
