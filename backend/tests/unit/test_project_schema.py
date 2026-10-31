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
    assert restored.schema_version == 1


def test_unknown_schema_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported project schema version"):
        migrate_project_document({"schema_version": 2})


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
