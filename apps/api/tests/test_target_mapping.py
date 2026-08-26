from oligospace_api.services.target_mapping import map_exact


def test_exact_forward_mapping() -> None:
    result = map_exact("AAGC", "TTAAGCGG")
    assert [(match.start, match.end, match.strand) for match in result.matches] == [(2, 6, "+")]
    assert result.warning is None


def test_reverse_complement_mapping() -> None:
    result = map_exact("AAGC", "TTGCTTGG")
    assert [(match.start, match.end, match.strand) for match in result.matches] == [(2, 6, "-")]


def test_ambiguous_mapping_reports_every_match() -> None:
    result = map_exact("ATG", "ATGAAAATG")
    assert result.match_count == 2
    assert result.ambiguous
    assert result.warning and "2 exact matches" in result.warning


def test_palindrome_is_not_double_counted() -> None:
    result = map_exact("ATAT", "ATAT")
    assert result.match_count == 1
