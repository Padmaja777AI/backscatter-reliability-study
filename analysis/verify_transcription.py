#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Padmaja Pabbathi
"""Check the CSV transcriptions against the text of the cited PDF pages.

For every transcribed value, the script extracts the text of the report page cited in
the CSV row (`source_report`, `source_page`) and checks that the value, exactly as
printed in the report, occurs among the numeric tokens on that page.  Leading zeros
are tolerated (the report prints one data rate as ".93").  This is a guard against
transcription slips; it cannot detect a value copied from the wrong cell of the same
page.

Requires PyMuPDF (`pip install pymupdf`).  Exit status 1 if any value is not found.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("PyMuPDF is required: pip install pymupdf")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reported"
REPORTS = ROOT / "docs" / "reports"

CHECKS = {
    "opt1_table1_per_position.csv": ["ber_reported_pct", "data_rate_reported_bytes_per_s", "duration_reported_s"],
    "opt1_table2_averages.csv": ["avg_ber_reported_pct", "avg_data_rate_reported_bytes_per_s", "avg_duration_reported_s"],
    "opt2_table1_per_position.csv": ["ber_reported_pct", "data_rate_reported_bytes_per_s", "prr_reported_pct"],
    "positions.csv": ["carrier_to_tag_cm", "tag_to_receiver_cm"],
}

_page_cache: dict[tuple[str, int], set[str]] = {}


def page_tokens(report: str, page: int) -> set[str]:
    key = (report, page)
    if key not in _page_cache:
        doc = pymupdf.open(REPORTS / report)
        text = doc[page - 1].get_text()
        _page_cache[key] = set(re.findall(r"\d*\.?\d+", text))
    return _page_cache[key]


def candidates(value: str) -> set[str]:
    value = value.strip()
    out = {value}
    if value.startswith("0."):
        out.add(value[1:])
    if "." in value:
        out.add(value.rstrip("0").rstrip("."))
    return out


def main() -> int:
    checked = found = 0
    missing: list[str] = []
    for csv_name, columns in CHECKS.items():
        with open(DATA / csv_name, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            report = row["source_report"].split(";")[0]
            page = int(row["source_page"])
            tokens = page_tokens(report, page)
            for col in columns:
                value = (row.get(col) or "").strip()
                if not value:
                    continue  # blank = printed as a dash / not reported
                checked += 1
                if candidates(value) & tokens:
                    found += 1
                else:
                    missing.append(f"{csv_name}: {row.get('config_id', '')} {row.get('position', '')} {col}={value} "
                                   f"not found on {report} page {page}")
    print(f"values checked: {checked}, found on the cited page: {found}, missing: {len(missing)}")
    for m in missing:
        print("  MISSING", m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
