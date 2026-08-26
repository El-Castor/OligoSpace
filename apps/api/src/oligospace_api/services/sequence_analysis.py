from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

IUPAC_DNA = frozenset("ACGTRYSWKMBDHVN")
UNAMBIGUOUS_DNA = frozenset("ACGT")
COMPLEMENT = str.maketrans("ACGTRYSWKMBDHVN", "TGCAYRSWMKVHDBN")
AVERAGE_RESIDUE_MASS = {"A": 313.21, "C": 289.18, "G": 329.21, "T": 304.20}


class InvalidSequenceError(ValueError):
    def __init__(self, invalid_symbols: set[str]) -> None:
        self.invalid_symbols = invalid_symbols
        super().__init__(f"Sequence contains invalid symbols: {', '.join(sorted(invalid_symbols))}")


@dataclass(frozen=True)
class SequenceMetrics:
    normalized_sequence: str
    length: int
    gc_percent: float | None
    melting_temperature_c: float | None
    molecular_weight_g_mol: float | None
    reverse_complement: str
    provenance: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_sequence(sequence: str) -> str:
    normalized = re.sub(r"\s+", "", sequence).upper()
    if not normalized:
        raise InvalidSequenceError(set())
    invalid = set(normalized) - IUPAC_DNA
    if invalid:
        raise InvalidSequenceError(invalid)
    return normalized


def reverse_complement(sequence: str) -> str:
    return normalize_sequence(sequence).translate(COMPLEMENT)[::-1]


def calculate_metrics(sequence: str) -> SequenceMetrics:
    normalized = normalize_sequence(sequence)
    unambiguous = set(normalized) <= UNAMBIGUOUS_DNA
    gc_percent = (
        round(100 * (normalized.count("G") + normalized.count("C")) / len(normalized), 2)
        if unambiguous
        else None
    )
    tm = (
        float(
            2 * (normalized.count("A") + normalized.count("T"))
            + 4 * (normalized.count("G") + normalized.count("C"))
        )
        if unambiguous
        else None
    )
    molecular_weight = (
        round(sum(AVERAGE_RESIDUE_MASS[base] for base in normalized) - 61.96, 2)
        if unambiguous
        else None
    )
    return SequenceMetrics(
        normalized_sequence=normalized,
        length=len(normalized),
        gc_percent=gc_percent,
        melting_temperature_c=tm,
        molecular_weight_g_mol=molecular_weight,
        reverse_complement=normalized.translate(COMPLEMENT)[::-1],
        provenance={
            "normalization": "uppercase-remove-unicode-whitespace/v1",
            "gc_method": "unambiguous-base-count/v1" if unambiguous else None,
            "tm_method": "wallace-2at-4gc/v1" if unambiguous else None,
            "molecular_weight_method": "average-ssdna-residue-mass-minus-61.96/v1"
            if unambiguous
            else None,
            "calculated_at": datetime.now(UTC).isoformat(),
        },
    )


def duplicate_relationship(candidate: str, existing: str) -> str | None:
    candidate_normalized = normalize_sequence(candidate)
    existing_normalized = normalize_sequence(existing)
    if candidate_normalized == existing_normalized:
        return "exact"
    if candidate_normalized == reverse_complement(existing_normalized):
        return "reverse_complement"
    return None
