"""Emit real golden-fixture facts from the unchanged worker, no interpretation."""

import argparse
import json
import platform
import re


def main():
    from oligospace_bioinfo import tasks

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--architecture", choices=["arm64", "amd64"], required=True)
    args = parser.parse_args()
    actual = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86_64": "amd64",
        "AMD64": "amd64",
    }.get(platform.machine())
    if actual != args.architecture or not re.fullmatch(r"[a-f0-9]{40}", args.source):
        raise ValueError("execution_identity_mismatch")
    parameters = {
        "mv_conc_mM": 50.0,
        "dv_conc_mM": 1.5,
        "dntp_conc_mM": 0.6,
        "dna_conc_nM": 50.0,
        "max_loop": 30,
        "max_nn_length": 60,
        "tm_method": "santalucia_1998",
        "salt_correction_method": "santalucia_1998",
    }
    inputs = {
        "forward": {"normalized_sequence": "ATGCGTACGTTAGCGTACGA"},
        "reverse": {"normalized_sequence": "TCGTACGCTAACGTACGCAT"},
    }
    result = tasks.primer3_analysis(
        "assay_primer3_pair_compatibility", inputs, parameters
    )
    print(
        json.dumps(
            {
                "source": args.source,
                "architecture": actual,
                "inputs": inputs,
                "parameters": parameters,
                "payload": result["payload"],
                "tool_version": result["provenance"]["tool_version"],
                "execution": "container_architecture_verified_runner_evidence_required",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
