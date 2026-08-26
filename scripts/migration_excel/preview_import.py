#!/usr/bin/env python3
"""Generate a deterministic, read-only JSON import preview."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oligospace_api.services.excel_import import preview_workbook


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    preview = preview_workbook(args.workbook)
    rendered = json.dumps(preview.as_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
