from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from typing import Any

from oligospace_bioinfo import __version__
from oligospace_bioinfo.celery_app import app

PRIMER3_VERSION = "2.6.1"
_UNAMBIGUOUS_DNA = re.compile(r"^[ACGT]+$")


def _run_tool(arguments: list[str]) -> str:
    completed = subprocess.run(
        arguments,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return completed.stdout.strip()


def _thermodynamic_tm(
    sequence: str,
    *,
    mode: str,
    mv_conc: float,
    dv_conc: float,
    dntp_conc: float,
    dna_conc: float,
) -> float:
    arguments = [
        "ntthal",
        "-r",
        "-a",
        mode,
        "-mv",
        str(mv_conc),
        "-dv",
        str(dv_conc),
        "-n",
        str(dntp_conc),
        "-d",
        str(dna_conc),
        "-s1",
        sequence,
    ]
    if mode != "HAIRPIN":
        arguments.extend(["-s2", sequence])
    return float(_run_tool(arguments))


def primer3_qc(
    sequence: str,
    *,
    mv_conc: float = 50.0,
    dv_conc: float = 1.5,
    dntp_conc: float = 0.6,
    dna_conc: float = 50.0,
) -> dict[str, Any]:
    """Return tool facts without interpreting experimental suitability."""
    normalized = "".join(sequence.split()).upper()
    if not _UNAMBIGUOUS_DNA.fullmatch(normalized):
        raise ValueError("Primer3 thermodynamic QC requires an unambiguous A/C/G/T sequence")

    started_at = datetime.now(UTC)
    shared_parameters = {
        "mv_conc": mv_conc,
        "dv_conc": dv_conc,
        "dntp_conc": dntp_conc,
        "dna_conc": dna_conc,
    }
    tm_c = float(
        _run_tool(
            [
                "oligotm",
                "-mv",
                str(mv_conc),
                "-dv",
                str(dv_conc),
                "-n",
                str(dntp_conc),
                "-d",
                str(dna_conc),
                normalized,
            ]
        )
    )
    return {
        "input": {"normalized_sequence": normalized},
        "result": {
            "tm_c": tm_c,
            "hairpin_tm_c": _thermodynamic_tm(normalized, mode="HAIRPIN", **shared_parameters),
            "homodimer_tm_c": _thermodynamic_tm(normalized, mode="ANY", **shared_parameters),
        },
        "provenance": {
            "worker_version": __version__,
            "tool": "Primer3",
            "tool_version": PRIMER3_VERSION,
            "parameters": {
                "mv_conc_mM": mv_conc,
                "dv_conc_mM": dv_conc,
                "dntp_conc_mM": dntp_conc,
                "dna_conc_nM": dna_conc,
                "tm_method": "SantaLucia 1998",
                "salt_correction": "SantaLucia 1998",
                "max_loop": 30,
            },
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
        },
        "interpretation": None,
    }


@app.task(name="oligospace.primer3_qc")  # type: ignore[misc]
def primer3_qc_task(sequence: str, parameters: dict[str, float] | None = None) -> dict[str, Any]:
    parameters = parameters or {}
    return primer3_qc(sequence, **parameters)
