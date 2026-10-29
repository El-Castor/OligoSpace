from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from oligospace_api.schemas.laboratory import ExperimentRunCreate, ValidationCreate
from oligospace_api.services.laboratory import ALLOWED_ATTACHMENT_TYPES


def test_validation_create_rejects_superseded_as_new_evidence() -> None:
    with pytest.raises(ValidationError):
        ValidationCreate.model_validate(
            {
                "assay_id": "10000000-0000-0000-0000-000000000001",
                "status": "superseded",
                "conclusion": "Invalid new evidence",
                "validated_at": datetime.now(UTC),
            }
        )


def test_experiment_run_schema_rejects_unknown_provenance_edits() -> None:
    payload = ExperimentRunCreate(
        assay_id=UUID("10000000-0000-0000-0000-000000000001"),
        performed_at=datetime.now(UTC),
        conditions={"annealing_temperature_c": 60},
    )
    assert payload.conditions["annealing_temperature_c"] == 60
    assert "application/pdf" in ALLOWED_ATTACHMENT_TYPES
    assert "application/x-msdownload" not in ALLOWED_ATTACHMENT_TYPES
