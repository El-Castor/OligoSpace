from __future__ import annotations

import subprocess
from typing import Any

import pytest

from oligospace_bioinfo import tasks

PARAMETERS: dict[str, Any] = {
    "mv_conc_mM": 50.0,
    "dv_conc_mM": 1.5,
    "dntp_conc_mM": 0.6,
    "dna_conc_nM": 50.0,
    "max_loop": 30,
    "max_nn_length": 60,
    "tm_method": "santalucia_1998",
    "salt_correction_method": "santalucia_1998",
}


def test_pair_contract_keeps_modes_orientation_and_facts_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(arguments: list[str]) -> str:
        calls.append(arguments)
        if arguments[:2] == ["primer3_core", "--about"]:
            return "Primer3 release 2.6.1"
        return "42.5"

    monkeypatch.setattr(tasks, "_run_tool", fake_run)
    result = tasks.primer3_analysis(
        "assay_primer3_pair_compatibility",
        {
            "forward": {"normalized_sequence": "ATGCGTACGTTAGC"},
            "reverse": {"normalized_sequence": "GCTAACGTACGCAT"},
        },
        PARAMETERS,
    )
    payload = result["payload"]
    assert payload["forward"]["nearest_neighbor_tm"]["method"].endswith("nearest_neighbor")
    assert payload["heterodimer"]["tool_mode"] == "ANY"
    assert payload["end_complementarity"]["tool_mode"] == "END1"
    assert payload["tm_delta"]["value"] == 0.0
    assert any(call[-2:] == ["-s2", "GCTAACGTACGCAT"] for call in calls)
    assert not any("reverse_complement" in " ".join(call) for call in calls)


def test_version_mismatch_is_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "_run_tool", lambda _: "Primer3 release 2.7.0")
    with pytest.raises(tasks.ScientificToolError, match="Expected Primer3") as raised:
        tasks.primer3_analysis(
            "oligo_primer3_qc",
            {"sequence": {"normalized": "ATGCGTACGTTAGC"}},
            PARAMETERS,
        )
    assert raised.value.code == "tool_version_mismatch"
    assert raised.value.retryable is False


def test_real_primer3_pair_golden_fixture() -> None:
    result = tasks.primer3_analysis(
        "assay_primer3_pair_compatibility",
        {
            "forward": {"normalized_sequence": "ATGCGTACGTTAGCGTACGA"},
            "reverse": {"normalized_sequence": "TCGTACGCTAACGTACGCAT"},
        },
        PARAMETERS,
    )
    payload = result["payload"]
    assert payload["forward"]["nearest_neighbor_tm"]["value"] == pytest.approx(59.626630, abs=1e-6)
    assert payload["forward"]["hairpin"]["value"] == pytest.approx(69.836183, abs=1e-6)
    assert payload["forward"]["homodimer"]["value"] == pytest.approx(46.168760, abs=1e-6)
    assert payload["reverse"]["nearest_neighbor_tm"]["value"] == pytest.approx(59.626630, abs=1e-6)
    assert payload["reverse"]["hairpin"]["value"] == pytest.approx(69.091431, abs=1e-6)
    assert payload["reverse"]["homodimer"]["value"] == pytest.approx(34.346077, abs=1e-6)
    assert payload["tm_delta"]["value"] == pytest.approx(0.0, abs=1e-6)
    assert payload["heterodimer"]["value"] == pytest.approx(59.555182, abs=1e-6)
    assert payload["end_complementarity"]["value"] == pytest.approx(59.555182, abs=1e-6)
    assert result["interpretation"] is None


def test_worker_rejects_ambiguous_and_overlong_sequences() -> None:
    with pytest.raises(tasks.ScientificToolError) as ambiguous:
        tasks._individual("ACGTN", PARAMETERS)
    assert ambiguous.value.code == "unsupported_sequence"
    with pytest.raises(tasks.ScientificToolError) as too_long:
        tasks._individual("A" * 61, PARAMETERS)
    assert too_long.value.code == "sequence_too_long"


def test_tool_failures_are_safely_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["oligotm"], timeout=30)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(tasks.ScientificToolError) as timed_out:
        tasks._run_tool(["oligotm", "ACGT"])
    assert timed_out.value.code == "tool_timeout"
    assert timed_out.value.retryable is True

    monkeypatch.setattr(tasks, "_run_tool", lambda _: "not-a-number")
    with pytest.raises(tasks.ScientificToolError) as malformed:
        tasks._number(["oligotm", "ACGT"])
    assert malformed.value.code == "invalid_tool_output"

    monkeypatch.setattr(tasks, "_run_tool", lambda _: "nan")
    with pytest.raises(tasks.ScientificToolError) as nonfinite:
        tasks._number(["oligotm", "ACGT"])
    assert nonfinite.value.code == "invalid_tool_output"
