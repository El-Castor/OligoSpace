import pytest

from oligospace_api.services.csv_export import spreadsheet_cell


@pytest.mark.parametrize("value", ["=1+1", "+cmd", "-1+2", "@SUM(A1)", " \t=1", "\r=1", "\n=1"])
def test_spreadsheet_formula_is_text(value: str) -> None:
    assert spreadsheet_cell(value) == "'" + value


@pytest.mark.parametrize("value", ["Bd21, floraison", 'name "quoted"', "échantillon", "ACGT", ""])
def test_plain_values_are_preserved(value: str) -> None:
    assert spreadsheet_cell(value) == value


def test_missing_and_zero_values_are_distinct() -> None:
    assert spreadsheet_cell(None) == ""
    assert spreadsheet_cell(0) == "0"
    assert spreadsheet_cell(0.0) == "0.0"
