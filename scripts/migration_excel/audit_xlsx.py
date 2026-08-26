#!/usr/bin/env python3
"""Read-only XLSX structural audit using only the Python standard library.

This intentionally small reader exists so Phase 0 can inspect the immutable source
workbook before the application's pinned openpyxl environment is created. It is not
the production importer.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_RE = re.compile(r"([A-Z]+)([0-9]+)")
IUPAC_DNA = frozenset("ACGTRYSWKMBDHVN")


def column_number(cell_ref: str) -> int:
    match = CELL_RE.fullmatch(cell_ref)
    if match is None:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    number = 0
    for char in match.group(1):
        number = number * 26 + ord(char) - ord("A") + 1
    return number


def text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


@dataclass(frozen=True)
class Sheet:
    name: str
    path: str


class WorkbookReader:
    def __init__(self, source: Path) -> None:
        self.archive = zipfile.ZipFile(source)
        self.shared_strings = self._read_shared_strings()
        self.sheets = self._read_sheets()

    def __enter__(self) -> WorkbookReader:
        return self

    def __exit__(self, *_: object) -> None:
        self.archive.close()

    def _read_shared_strings(self) -> list[str]:
        try:
            root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        except KeyError:
            return []
        return [text_content(item) for item in root.findall(f"{{{MAIN_NS}}}si")]

    def _read_sheets(self) -> list[Sheet]:
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(self.archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relationship.attrib["Id"]: relationship.attrib["Target"]
            for relationship in relationships.findall(f"{{{PKG_REL_NS}}}Relationship")
        }
        sheets: list[Sheet] = []
        for element in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
            rel_id = element.attrib[f"{{{REL_NS}}}id"]
            target = targets[rel_id].lstrip("/")
            path = target if target.startswith("xl/") else f"xl/{target}"
            sheets.append(Sheet(name=element.attrib["name"], path=path))
        return sheets

    def rows(self, sheet: Sheet) -> list[list[object | None]]:
        root = ET.fromstring(self.archive.read(sheet.path))
        rows: list[list[object | None]] = []
        for row in root.findall(f".//{{{MAIN_NS}}}row"):
            values: dict[int, object | None] = {}
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                reference = cell.attrib["r"]
                cell_type = cell.attrib.get("t")
                value = cell.find(f"{{{MAIN_NS}}}v")
                inline = cell.find(f"{{{MAIN_NS}}}is")
                raw = text_content(inline) if inline is not None else text_content(value)
                if cell_type == "s" and raw:
                    parsed: object | None = self.shared_strings[int(raw)]
                elif cell_type == "b":
                    parsed = raw == "1"
                elif cell_type in {"inlineStr", "str", "e"}:
                    parsed = raw
                elif raw == "":
                    parsed = None
                else:
                    try:
                        parsed = int(raw)
                    except ValueError:
                        try:
                            parsed = float(raw)
                        except ValueError:
                            parsed = raw
                values[column_number(reference)] = parsed
            if values:
                width = max(values)
                rows.append([values.get(index) for index in range(1, width + 1)])
        return rows


def migration_audit(rows: list[list[object | None]]) -> dict[str, object]:
    """Summarize the source rows without changing or accepting any record."""
    if not rows:
        return {}
    headers = [str(value) if value is not None else "" for value in rows[0]]
    records = [dict(zip(headers, row, strict=False)) for row in rows[1:]]
    allocated_only = [
        record
        for record in records
        if record.get("Oligo_ID")
        and not any(value not in (None, "") for key, value in record.items() if key != "Oligo_ID")
    ]
    populated = [record for record in records if record not in allocated_only]
    candidates = [record for record in populated if record.get("Oligo_ID")]

    applications = Counter(
        str(row.get("Application")) for row in candidates if row.get("Application")
    )
    directions = Counter(str(row.get("Direction")) for row in candidates if row.get("Direction"))
    validation = Counter(
        str(row.get("Validation_status")) for row in candidates if row.get("Validation_status")
    )
    invalid_sequences: list[dict[str, object]] = []
    missing_sequences: list[str] = []
    missing_names: list[str] = []
    length_mismatches: list[dict[str, object]] = []
    normalized_sequences: defaultdict[str, list[str]] = defaultdict(list)
    locations: defaultdict[str, list[str]] = defaultdict(list)

    for row in candidates:
        oligo_id = str(row["Oligo_ID"])
        name = row.get("Oligo_Name")
        sequence = row.get("Sequence_5to3")
        if not name:
            missing_names.append(oligo_id)
        if not sequence:
            missing_sequences.append(oligo_id)
        else:
            source_sequence = str(sequence)
            normalized = re.sub(r"\s+", "", source_sequence).upper()
            invalid = sorted(set(normalized) - IUPAC_DNA)
            if invalid:
                invalid_sequences.append(
                    {
                        "oligo_id": oligo_id,
                        "source": source_sequence,
                        "invalid_symbols": invalid,
                    }
                )
            else:
                normalized_sequences[normalized].append(oligo_id)
                entered_length = row.get("Length_nt")
                if entered_length not in (None, "") and int(entered_length) != len(normalized):
                    length_mismatches.append(
                        {
                            "oligo_id": oligo_id,
                            "entered": entered_length,
                            "calculated": len(normalized),
                        }
                    )
        location = row.get("Location")
        if location:
            locations[str(location).strip()].append(oligo_id)

    return {
        "candidate_rows": len(candidates),
        "allocated_id_only_rows": len(allocated_only),
        "applications": dict(applications),
        "directions": dict(directions),
        "validation_statuses": dict(validation),
        "template_or_example_ids": [
            str(row["Oligo_ID"]) for row in candidates if str(row["Oligo_ID"]).endswith("EX")
        ],
        "missing_names": missing_names,
        "missing_sequences": missing_sequences,
        "invalid_sequences": invalid_sequences,
        "length_mismatches": length_mismatches,
        "exact_sequence_duplicates": {
            sequence: ids for sequence, ids in normalized_sequences.items() if len(ids) > 1
        },
        "storage_conflicts": {location: ids for location, ids in locations.items() if len(ids) > 1},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--rows", action="store_true", help="Include all non-empty rows")
    args = parser.parse_args()

    result: dict[str, object] = {"source": str(args.workbook), "sheets": []}
    with WorkbookReader(args.workbook) as workbook:
        sheet_results: list[dict[str, object]] = []
        for sheet in workbook.sheets:
            rows = workbook.rows(sheet)
            sheet_result: dict[str, object] = {
                "name": sheet.name,
                "non_empty_rows": len(rows),
                "max_columns": max((len(row) for row in rows), default=0),
                "first_rows": rows[:5],
            }
            if args.rows:
                sheet_result["rows"] = rows
            if sheet.name == "Oligo-probes CP database":
                sheet_result["migration_audit"] = migration_audit(rows)
            sheet_results.append(sheet_result)
        result["sheets"] = sheet_results
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
