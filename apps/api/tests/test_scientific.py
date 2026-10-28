from __future__ import annotations

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from oligospace_api.schemas.scientific import Primer3Parameters
from oligospace_api.services.scientific_contract import (
    canonical_sha256,
    sequence_sha256,
    validate_sequence,
)


def test_primer3_parameters_expand_reproducible_defaults() -> None:
    parameters = Primer3Parameters()
    assert parameters.tm_method == "santalucia_1998"
    assert parameters.salt_correction_method == "santalucia_1998"
    assert parameters.max_nn_length == 60
    assert parameters.model_dump()["dna_conc_nM"] == 50.0


def test_primer3_parameters_reject_unknown_unbounded_and_invalid_ions() -> None:
    with pytest.raises(ValidationError):
        Primer3Parameters.model_validate({"raw_cli_arguments": "--unsafe"})
    with pytest.raises(ValidationError):
        Primer3Parameters(max_loop=101)
    with pytest.raises(ValidationError):
        Primer3Parameters(dv_conc_mM=0.5, dntp_conc_mM=0.6)


def test_scientific_fingerprints_are_canonical_and_sequence_specific() -> None:
    assert canonical_sha256({"b": 2, "a": 1}) == canonical_sha256({"a": 1, "b": 2})
    assert sequence_sha256("ACGT") != sequence_sha256("TGCA")


def test_primer3_sequence_contract_enforces_alphabet_and_nn_boundaries() -> None:
    validate_sequence("A" * 60, max_nn_length=60)
    with pytest.raises(HTTPException) as too_long:
        validate_sequence("A" * 61, max_nn_length=60)
    assert too_long.value.detail["code"] == "primer3_sequence_too_long"
    with pytest.raises(HTTPException) as ambiguous:
        validate_sequence("ACGTN", max_nn_length=60)
    assert ambiguous.value.detail["code"] == "primer3_unsupported_sequence"
