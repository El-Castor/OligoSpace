from oligospace_api.services.excel_import import preview_records


def test_import_preview_normalizes_and_does_not_import() -> None:
    preview = preview_records(
        [
            {
                "Oligo_ID": "O0001",
                "Oligo_Name": "Primer A",
                "Sequence_5to3": " acgt ",
                "Direction": "F",
                "Length_nt": 4,
                "Location": "Box/A1",
            },
            {"Oligo_ID": "O0002"},
        ]
    )
    assert preview.candidate_rows == 1
    assert preview.importable_rows == 1
    assert preview.allocated_only_rows == 1
    assert preview.rejected_candidate_rows == 0
    assert preview.skipped_rows == 1
    assert preview.imported_rows == 0
    assert preview.normalized_records[0]["normalized_sequence"] == "ACGT"
    assert any(issue.code == "normalized_direction" for issue in preview.issues)


def test_invalid_sequences_and_storage_conflicts_are_reported() -> None:
    preview = preview_records(
        [
            {
                "Oligo_ID": "O0001",
                "Oligo_Name": "Bad",
                "Sequence_5to3": "not a sequence.",
                "Location": "Box/A1",
            },
            {
                "Oligo_ID": "O0002",
                "Oligo_Name": "Good",
                "Sequence_5to3": "AAGC",
                "Location": "Box/A1",
            },
        ]
    )
    codes = {issue.code for issue in preview.issues}
    assert "invalid_sequence" in codes
    assert "storage_conflict" in codes
    assert preview.importable_rows == 1
    assert preview.rejected_candidate_rows == 1
