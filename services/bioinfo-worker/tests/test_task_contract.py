import pytest

from oligospace_bioinfo.tasks import primer3_qc, primer3_qc_task, scientific_job_task


def test_task_has_stable_public_name() -> None:
    assert primer3_qc_task.name == "oligospace.primer3_qc"
    assert scientific_job_task.name == "oligospace.scientific_job"


def test_primer3_result_separates_facts_from_interpretation() -> None:
    result = primer3_qc("ATGCGTACGTTAGC")

    assert result["input"]["normalized_sequence"] == "ATGCGTACGTTAGC"
    assert result["provenance"]["tool"] == "Primer3"
    assert isinstance(result["result"]["tm_c"], float)
    assert isinstance(result["result"]["hairpin_tm_c"], float)
    assert isinstance(result["result"]["homodimer_tm_c"], float)
    assert result["result"]["tm_c"] == pytest.approx(45.975298, abs=1e-6)
    assert result["result"]["hairpin_tm_c"] == pytest.approx(0.0, abs=1e-6)
    assert result["result"]["homodimer_tm_c"] == pytest.approx(17.904042, abs=1e-6)
    assert result["interpretation"] is None
