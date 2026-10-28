from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from fastapi import HTTPException

PARAMETER_SCHEMA_VERSION = "primer3-parameters-v1"
RESULT_SCHEMA_VERSION = "primer3-results-v1"
WRAPPER_CONTRACT_VERSION = "primer3-cli-v1"
PRIMER3_VERSION = "2.6.1"
_DNA = re.compile(r"^[ACGT]+$")


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def sequence_sha256(sequence: str) -> str:
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def validate_sequence(sequence: str, *, max_nn_length: int) -> None:
    if not _DNA.fullmatch(sequence):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "primer3_unsupported_sequence",
                "message": "Primer3 analysis requires unambiguous DNA (A/C/G/T).",
            },
        )
    if len(sequence) > max_nn_length:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "primer3_sequence_too_long",
                "message": (
                    f"Nearest-neighbor analysis is qualified for at most {max_nn_length} nt."
                ),
            },
        )
