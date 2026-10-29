from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from oligospace_api.models.enums import (
    ScientificAttemptStatus,
    ScientificJobKind,
    ScientificJobStatus,
)


class Primer3Parameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mv_conc_mM: float = Field(default=50.0, ge=0.0, le=1000.0, allow_inf_nan=False)
    dv_conc_mM: float = Field(default=1.5, ge=0.0, le=100.0, allow_inf_nan=False)
    dntp_conc_mM: float = Field(default=0.6, ge=0.0, le=100.0, allow_inf_nan=False)
    dna_conc_nM: float = Field(default=50.0, gt=0.0, le=100000.0, allow_inf_nan=False)
    max_loop: int = Field(default=30, ge=0, le=100)
    max_nn_length: int = Field(default=60, ge=10, le=60)
    tm_method: Literal["santalucia_1998"] = "santalucia_1998"
    salt_correction_method: Literal["santalucia_1998"] = "santalucia_1998"

    @model_validator(mode="after")
    def validate_ions(self) -> Primer3Parameters:
        if self.dv_conc_mM > 0 and self.dntp_conc_mM > self.dv_conc_mM:
            raise ValueError("dntp_conc_mM must not exceed dv_conc_mM")
        return self


class OligoPrimer3JobCreate(BaseModel):
    oligo_public_id: str = Field(pattern=r"^[A-Za-z]{3}-[0-9]{6,}$", max_length=32)
    parameters: Primer3Parameters | None = None


class AssayPrimer3PairJobCreate(BaseModel):
    assay_public_id: str = Field(pattern=r"^[A-Za-z]{3}-[0-9]{6,}$", max_length=32)
    forward_oligo_id: uuid.UUID | None = None
    reverse_oligo_id: uuid.UUID | None = None
    parameters: Primer3Parameters | None = None


class ScientificAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_number: int
    state: ScientificAttemptStatus
    task_id: str | None
    claimed_at: datetime
    lease_expires_at: datetime
    started_at: datetime
    completed_at: datetime | None
    retryable: bool
    tool_version: str | None
    worker_version: str | None
    wrapper_contract_version: str | None
    build_identity: str | None
    exit_status: int | None
    error_code: str | None
    error_summary: str | None


class ScientificResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    result_schema_version: str
    payload: dict[str, Any]
    warnings: list[dict[str, Any]]
    algorithm: str
    tool_version: str
    tool_source_sha256: str
    worker_version: str
    wrapper_contract_version: str
    build_identity: str
    started_at: datetime
    completed_at: datetime
    executed_at: datetime


class ScientificJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_id: str
    requester_id: uuid.UUID
    kind: ScientificJobKind
    state: ScientificJobStatus
    visibility: str
    owner_team_id: uuid.UUID | None
    owner_project_id: uuid.UUID | None
    oligo_id: uuid.UUID | None
    assay_id: uuid.UUID | None
    forward_oligo_id: uuid.UUID | None
    reverse_oligo_id: uuid.UUID | None
    assay_version: int | None
    input_snapshot: dict[str, Any]
    input_sha256: str
    requested_parameters: dict[str, Any]
    effective_parameters: dict[str, Any]
    parameter_schema_version: str
    execution_fingerprint: str
    celery_task_id: str | None
    attempt_count: int
    max_attempts: int
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_error_code: str | None
    last_error_summary: str | None
    created_at: datetime
    updated_at: datetime
    attempts: list[ScientificAttemptRead]
    result: ScientificResultRead | None


class ScientificJobPage(BaseModel):
    items: list[ScientificJobRead]
    total: int
    limit: int
    offset: int
