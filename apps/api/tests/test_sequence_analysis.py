import math

import pytest

from oligospace_api.services.sequence_analysis import (
    InvalidSequenceError,
    calculate_metrics,
    duplicate_relationship,
    normalize_sequence,
    reverse_complement,
)


def test_normalize_sequence_removes_whitespace_and_preserves_iupac() -> None:
    assert normalize_sequence(" acgt\nRY ") == "ACGTRY"


def test_invalid_sequence_is_rejected() -> None:
    with pytest.raises(InvalidSequenceError) as error:
        normalize_sequence("Pas spécifique a refaire.")
    assert "." in error.value.invalid_symbols


def test_metrics_are_reproducible_and_labeled() -> None:
    metrics = calculate_metrics("ATGC")
    assert metrics.length == 4
    assert math.isclose(metrics.gc_percent or 0, 50.0)
    assert math.isclose(metrics.melting_temperature_c or 0, 12.0)
    assert math.isclose(metrics.molecular_weight_g_mol or 0, 1173.84)
    assert metrics.reverse_complement == "GCAT"
    assert metrics.provenance["tm_method"] == "wallace-2at-4gc/v1"


def test_ambiguous_sequence_omits_unsupported_calculations() -> None:
    metrics = calculate_metrics("ACGN")
    assert metrics.gc_percent is None
    assert metrics.melting_temperature_c is None
    assert metrics.molecular_weight_g_mol is None


def test_reverse_complement_and_duplicate_relationships() -> None:
    assert reverse_complement("ARYN") == "NRYT"
    assert duplicate_relationship("acgt", "ACGT") == "exact"
    assert duplicate_relationship("AAGC", "GCTT") == "reverse_complement"
    assert duplicate_relationship("AAAA", "CCCC") is None
