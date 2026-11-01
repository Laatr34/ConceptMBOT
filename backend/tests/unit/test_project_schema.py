from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.projects import ProjectDocument, migrate_project_document


def test_project_document_is_versioned_and_round_trips() -> None:
    now = datetime.now(UTC)
    document = ProjectDocument(
        id=uuid4(),
        name="Prototype",
        created_at=now,
        updated_at=now,
        data={},
    )
    restored = migrate_project_document(document.model_dump(mode="json"))
    assert restored == document
    assert restored.schema_version == 2
    assert restored.data["mechanical"] == {"mass_points": [], "contacts": []}


def test_v1_project_migrates_without_losing_existing_data() -> None:
    now = datetime.now(UTC)
    raw = {
        "schema_version": 1,
        "id": str(uuid4()),
        "name": "Legacy robot",
        "description": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "data": {"notes": "keep this", "custom": {"enabled": True}},
    }

    migrated = migrate_project_document(raw)

    assert migrated.schema_version == 2
    assert migrated.data["notes"] == "keep this"
    assert migrated.data["custom"] == {"enabled": True}
    assert migrated.data["mechanical"] == {"mass_points": [], "contacts": []}


def test_unknown_schema_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported project schema version"):
        migrate_project_document({"schema_version": 3})


def test_unknown_top_level_fields_are_rejected() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        ProjectDocument(
            id=uuid4(),
            name="Prototype",
            created_at=now,
            updated_at=now,
            undocumented_field=True,
        )


def test_mechanical_layout_rejects_unknown_fields() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        ProjectDocument(
            id=uuid4(),
            name="Prototype",
            created_at=now,
            updated_at=now,
            data={"mechanical": {"unknown": True}},
        )


def test_mechanical_layout_preserves_unknown_measurements_as_null() -> None:
    now = datetime.now(UTC)
    document = ProjectDocument(
        id=uuid4(),
        name="Prototype",
        created_at=now,
        updated_at=now,
        data={
            "mechanical": {
                "mass_points": [{"name": "Raspberry Pi", "mass_kg": None, "x_m": None}],
                "contacts": [{"name": "caster", "x_m": None, "y_m": None}],
            }
        },
    )

    point = document.data["mechanical"]["mass_points"][0]
    contact = document.data["mechanical"]["contacts"][0]
    assert point["mass_kg"] is None
    assert point["x_m"] is None
    assert contact["x_m"] is None
    assert contact["y_m"] is None
