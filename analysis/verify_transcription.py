#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Padmaja Pabbathi
"""Verify the CSV transcriptions in data/reported/ against the report PDFs.

Three checks are performed.

1. CELL CHECK (report-specific).  Each cited table is parsed from the PDF's text layer
   by position on the page: every printed table row is one text line, the row's
   configuration comes from the label words printed in the first column of its row
   group, the position comes from the P1–P5 token, and the metric columns are read in
   the table's printed column order.  The expected values therefore come from the PDF
   alone, never from the CSV being checked.  For each CSV file the check requires that
   - the cited report file exists, the cited page is the page on which the table's
     header line was found, and the cited table label matches;
   - the CSV holds exactly the expected (configuration, position) rows: none missing,
     none duplicated, none extra;
   - every value equals the parsed cell for its (configuration, position, metric), and
     a blank CSV cell corresponds to a printed dash;
   - the reception flag is `none` exactly on rows where the report prints its failure
     marker (BER 100.00, D/R 0.00 and a dash in the last column) and `received`
     elsewhere;
   - the normalised `ber_pct` equals the printed BER on received rows and is blank on
     rows without reception.
2. TOKEN CHECK (weak, supplementary).  Every value occurs somewhere among the numeric
   tokens of the cited page.  This cannot detect a value copied into the wrong row or
   column; it is kept only as a coarse guard.
3. SELF-TEST (`--self-test`).  In-memory copies of the CSVs are mutated: two different
   values on the same source page are swapped, a reception flag is flipped, a
   normalised BER is altered and a source page is changed.  The cell check must fail on
   every mutation, and the run reports whether the token check would have noticed the
   swap (it does not).

What passing establishes: the CSV files equal the values printed in the reports'
tables, cell by cell, as far as the PDF text layer represents them.  It does not
establish that the reports' values are themselves correct, and it cannot detect an
error that the reports contain.

Requires PyMuPDF (`pip install pymupdf`).  Exit status 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("PyMuPDF is required: pip install pymupdf")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reported"
REPORTS = ROOT / "docs" / "reports"
POSITIONS = ["P1", "P2", "P3", "P4", "P5"]
DASH = "—"

OPT1 = "Group6_Experimental_Optimisation_1_Baud_Rate.pdf"
OPT2 = "Group6_Experimental_Optimisation_2_250kBaud_Longer_Packets.pdf"

# Report-specific description of each transcribed table.  `header` is the printed
# header line used to find the page; `labels` maps the printed first-column label to
# the CSV config_id; `metrics` are the CSV columns in the table's printed column order.
SPECS = {
    "opt1_table1_per_position.csv": {
        "kind": "position_table", "report": OPT1, "table": "Table 1",
        "header": "Baud Rate Position BER (%) D/R (byte/s) Time (s)",
        "labels": {"100k (baseline)": "100k", "80k": "80k", "70k": "70k", "60k": "60k", "50k": "50k"},
        "metrics": ["ber_reported_pct", "data_rate_reported_bytes_per_s", "duration_reported_s"],
    },
    "opt1_table2_averages.csv": {
        "kind": "config_table", "report": OPT1, "table": "Table 2",
        "header": "Baud Rate Avg BER (%) Avg D/R (byte/s) Avg Time (s)",
        "labels": {"100k (baseline)": "100k", "80k": "80k", "70k": "70k", "60k": "60k", "50k": "50k"},
        "metrics": ["avg_ber_reported_pct", "avg_data_rate_reported_bytes_per_s", "avg_duration_reported_s"],
    },
    "opt2_table1_per_position.csv": {
        "kind": "position_table", "report": OPT2, "table": "Table 1",
        "header": "Baud Rate Position BER (%) D/R (byte/s) Packet Reception Rate (%)",
        "labels": {"100k (baseline)": "100k", "250k and increased packet length": "250k_long"},
        "metrics": ["ber_reported_pct", "data_rate_reported_bytes_per_s", "prr_reported_pct"],
    },
    "positions.csv": {
        "kind": "positions", "reports": [OPT1, OPT2],
        "metrics": ["carrier_to_tag_cm", "tag_to_receiver_cm"],
    },
}


# --------------------------------------------------------------------------- #
# PDF parsing                                                                  #
# --------------------------------------------------------------------------- #
def page_lines(doc, page_no: int) -> list[list[str]]:
    """Text lines of a page as token lists, in reading order (top to bottom, left to right)."""
    words = sorted(doc[page_no - 1].get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines: list[list[tuple[float, str]]] = []
    centres: list[float] = []
    for x0, y0, x1, y1, text, *_ in words:
        yc = (y0 + y1) / 2
        if lines and abs(centres[-1] - yc) <= 3.0:
            lines[-1].append((x0, text))
        else:
            lines.append([(x0, text)])
            centres.append(yc)
    return [[t for _, t in sorted(line)] for line in lines]


def find_table_page(doc, header: str) -> tuple[int, int]:
    """Return (page number, line index) of the printed header line."""
    for page_no in range(1, doc.page_count + 1):
        for idx, tokens in enumerate(page_lines(doc, page_no)):
            if " ".join(tokens) == header:
                return page_no, idx
    raise ValueError(f"header line not found in {doc.name}: {header!r}")


def normalise(printed: str) -> str:
    """Printed cell -> comparable string: dash -> blank, '.93' -> '0.93'."""
    if printed == DASH:
        return ""
    return "0" + printed if printed.startswith(".") else printed


def parse_position_table(doc, spec) -> tuple[int, dict[tuple[str, str], dict[str, str]]]:
    """Rows keyed by (config_id, position) -> {metric: printed value}; also the page."""
    page_no, header_idx = find_table_page(doc, spec["header"])
    n = len(spec["metrics"])
    row_re = re.compile(r"^P[1-5]$")
    groups: list[dict] = []
    for tokens in page_lines(doc, page_no)[header_idx + 1:]:
        pos_idx = next((i for i, t in enumerate(tokens) if row_re.match(t)), None)
        if pos_idx is None or len(tokens) - pos_idx - 1 != n:
            if groups:  # table ended
                break
            continue
        position = tokens[pos_idx]
        label = " ".join(tokens[:pos_idx])
        values = tokens[pos_idx + 1:]
        if position == "P1":
            groups.append({"label": "", "rows": {}})
        if label:
            groups[-1]["label"] = label
        groups[-1]["rows"][position] = dict(zip(spec["metrics"], values))
    cells: dict[tuple[str, str], dict[str, str]] = {}
    for g in groups:
        if g["label"] not in spec["labels"]:
            raise ValueError(f"unexpected row-group label {g['label']!r} in {spec['report']} {spec['table']}")
        cfg = spec["labels"][g["label"]]
        for position, vals in g["rows"].items():
            cells[(cfg, position)] = vals
    return page_no, cells


def parse_config_table(doc, spec) -> tuple[int, dict[tuple[str, str], dict[str, str]]]:
    page_no, header_idx = find_table_page(doc, spec["header"])
    n = len(spec["metrics"])
    cells: dict[tuple[str, str], dict[str, str]] = {}
    for tokens in page_lines(doc, page_no)[header_idx + 1:]:
        if len(tokens) <= n:
            break
        label, values = " ".join(tokens[:-n]), tokens[-n:]
        if label not in spec["labels"]:
            break
        cells[(spec["labels"][label], "")] = dict(zip(spec["metrics"], values))
    return page_no, cells


def parse_positions(doc) -> tuple[int, dict[tuple[str, str], dict[str, str]]]:
    """'• P1: 27 cm / 273 cm' lines -> {(P1, ''): {carrier..: '27', tag..: '273'}}."""
    pat = re.compile(r"^• (P[1-5]): (\d+) cm / (\d+) cm")
    for page_no in range(1, doc.page_count + 1):
        cells = {}
        for tokens in page_lines(doc, page_no):
            m = pat.match(" ".join(tokens))
            if m:
                cells[(m.group(1), "")] = {"carrier_to_tag_cm": m.group(2), "tag_to_receiver_cm": m.group(3)}
        if len(cells) == 5:
            return page_no, cells
    raise ValueError(f"position list not found in {doc.name}")


# --------------------------------------------------------------------------- #
# Checks                                                                       #
# --------------------------------------------------------------------------- #
def same_value(csv_value: str, printed: str) -> bool:
    expected = normalise(printed)
    if csv_value == "" or expected == "":
        return csv_value == expected
    try:
        return Decimal(csv_value) == Decimal(expected)
    except InvalidOperation:
        return csv_value == expected


def cell_check(name: str, rows: list[dict]) -> list[str]:
    spec = SPECS[name]
    errors: list[str] = []
    kind = spec["kind"]

    if kind == "positions":
        expected_by_report = {}
        for report in spec["reports"]:
            doc = pymupdf.open(REPORTS / report)
            expected_by_report[report] = parse_positions(doc)
        seen = set()
        for r in rows:
            key = (r["position"], "")
            if key in seen:
                errors.append(f"{name}: duplicate row {r['position']}")
            seen.add(key)
            cited = r["source_report"].split(";")
            for report in cited:
                if report not in expected_by_report:
                    errors.append(f"{name}: {r['position']} cites unknown report {report}")
                    continue
                page_no, cells = expected_by_report[report]
                if int(r["source_page"]) != page_no:
                    errors.append(f"{name}: {r['position']} cites page {r['source_page']} of {report}, list is on page {page_no}")
                if key not in cells:
                    errors.append(f"{name}: {r['position']} not in the printed list of {report}")
                    continue
                for metric in spec["metrics"]:
                    if not same_value(r[metric], cells[key][metric]):
                        errors.append(f"{name}: {r['position']} {metric}={r[metric]!r} but {report} prints {cells[key][metric]!r}")
        for report, (page_no, cells) in expected_by_report.items():
            for key in cells:
                if key not in seen:
                    errors.append(f"{name}: missing row {key[0]} (printed in {report})")
        return errors

    doc = pymupdf.open(REPORTS / spec["report"])
    page_no, cells = parse_position_table(doc, spec) if kind == "position_table" else parse_config_table(doc, spec)
    expected_keys = set(cells)
    if kind == "position_table":
        wanted = {(cfg, p) for cfg in spec["labels"].values() for p in POSITIONS}
    else:
        wanted = {(cfg, "") for cfg in spec["labels"].values()}
    if expected_keys != wanted:
        errors.append(f"{name}: parser found {sorted(expected_keys)} but expected {sorted(wanted)} in the PDF")

    seen = set()
    for r in rows:
        key = (r["config_id"], r.get("position", ""))
        tag = f"{name}: {key[0]} {key[1]}".rstrip()
        if key in seen:
            errors.append(f"{tag}: duplicate row")
        seen.add(key)
        # source references
        if r["source_report"] != spec["report"] or not (REPORTS / r["source_report"]).exists():
            errors.append(f"{tag}: source_report {r['source_report']!r} is not {spec['report']!r}")
        if int(r["source_page"]) != page_no:
            errors.append(f"{tag}: source_page {r['source_page']} but the table is on page {page_no}")
        if r["source_table"] != spec["table"]:
            errors.append(f"{tag}: source_table {r['source_table']!r} is not {spec['table']!r}")
        if key not in cells:
            errors.append(f"{tag}: no such row in the printed table")
            continue
        printed = cells[key]
        # values
        for metric in spec["metrics"]:
            if not same_value(r[metric], printed[metric]):
                errors.append(f"{tag}: {metric}={r[metric]!r} but the PDF cell prints {printed[metric]!r}")
        # reception flag and normalised BER
        if kind == "position_table":
            m = spec["metrics"]
            failure_row = printed[m[0]] == "100.00" and printed[m[1]] == "0.00" and printed[m[2]] == DASH
            expected_flag = "none" if failure_row else "received"
            if r["reception"] != expected_flag:
                errors.append(f"{tag}: reception={r['reception']!r} but the printed row implies {expected_flag!r}")
            if failure_row:
                if r["ber_pct"] != "":
                    errors.append(f"{tag}: ber_pct should be blank on a no-reception row, got {r['ber_pct']!r}")
            elif not same_value(r["ber_pct"], printed[m[0]]):
                errors.append(f"{tag}: ber_pct={r['ber_pct']!r} does not equal the printed BER {printed[m[0]]!r}")
    for key in cells:
        if key not in seen:
            errors.append(f"{name}: missing row {key}")
    return errors


def token_check(name: str, rows: list[dict]) -> tuple[int, int, list[str]]:
    spec = SPECS[name]
    metrics = spec["metrics"]
    cache: dict[tuple[str, int], set[str]] = {}
    checked = found = 0
    missing = []
    for r in rows:
        report = r["source_report"].split(";")[0]
        page = int(r["source_page"])
        if (report, page) not in cache:
            text = pymupdf.open(REPORTS / report)[page - 1].get_text()
            cache[(report, page)] = set(re.findall(r"\d*\.?\d+", text))
        tokens = cache[(report, page)]
        for metric in metrics:
            value = r[metric].strip()
            if not value:
                continue
            checked += 1
            cands = {value, value[1:] if value.startswith("0.") else value}
            if cands & tokens:
                found += 1
            else:
                missing.append(f"{name}: {r.get('config_id', '')} {r.get('position', '')} {metric}={value}")
    return checked, found, missing


def load(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# Self-test: mutations that must be caught                                     #
# --------------------------------------------------------------------------- #
def self_test() -> bool:
    ok = True

    def expect_failure(label: str, name: str, rows: list[dict], token_note: bool = False) -> None:
        nonlocal ok
        errs = cell_check(name, rows)
        status = "detected" if errs else "NOT DETECTED"
        ok = ok and bool(errs)
        print(f"  {label}: cell check {status} ({len(errs)} finding(s))")
        for e in errs[:3]:
            print(f"      {e}")
        if token_note:
            _, _, missing = token_check(name, rows)
            print(f"      token check on the same mutation: {'would NOT notice' if not missing else 'would notice'}")

    print("self-test: mutating in-memory copies of the CSVs")
    rows = deepcopy(load("opt1_table1_per_position.csv"))
    a = next(r for r in rows if r["config_id"] == "80k" and r["position"] == "P1")
    b = next(r for r in rows if r["config_id"] == "80k" and r["position"] == "P2")
    assert a["ber_reported_pct"] != b["ber_reported_pct"]
    a["ber_reported_pct"], b["ber_reported_pct"] = b["ber_reported_pct"], a["ber_reported_pct"]
    a["ber_pct"], b["ber_pct"] = b["ber_pct"], a["ber_pct"]
    expect_failure("swap 80k P1 and 80k P2 BER (same page, same column)", "opt1_table1_per_position.csv", rows, token_note=True)

    rows = deepcopy(load("opt1_table1_per_position.csv"))
    a = next(r for r in rows if r["config_id"] == "80k" and r["position"] == "P1")
    b = next(r for r in rows if r["config_id"] == "60k" and r["position"] == "P1")
    a["duration_reported_s"], b["duration_reported_s"] = b["duration_reported_s"], a["duration_reported_s"]
    expect_failure("swap 80k P1 and 60k P1 duration (same page, different row groups)", "opt1_table1_per_position.csv", rows, token_note=True)

    rows = deepcopy(load("opt1_table1_per_position.csv"))
    a = next(r for r in rows if r["config_id"] == "70k" and r["position"] == "P1")
    a["data_rate_reported_bytes_per_s"], a["duration_reported_s"] = a["duration_reported_s"], a["data_rate_reported_bytes_per_s"]
    expect_failure("swap D/R and duration within 70k P1 (same row, different columns)", "opt1_table1_per_position.csv", rows, token_note=True)

    rows = deepcopy(load("opt2_table1_per_position.csv"))
    a = next(r for r in rows if r["config_id"] == "250k_long" and r["position"] == "P4")
    a["reception"] = "none"
    expect_failure("flip reception flag on 250k P4", "opt2_table1_per_position.csv", rows)

    rows = deepcopy(load("opt1_table1_per_position.csv"))
    a = next(r for r in rows if r["config_id"] == "50k" and r["position"] == "P5")
    a["ber_pct"] = "14.96"
    expect_failure("alter normalised ber_pct on 50k P5", "opt1_table1_per_position.csv", rows)

    rows = deepcopy(load("opt1_table2_averages.csv"))
    rows[2]["source_page"] = "4"
    expect_failure("cite the wrong page for 70k in Table 2", "opt1_table2_averages.csv", rows)

    rows = deepcopy(load("opt1_table1_per_position.csv"))
    rows.append(deepcopy(rows[0]))
    expect_failure("duplicate the 100k P1 row", "opt1_table1_per_position.csv", rows)

    rows = deepcopy(load("opt1_table1_per_position.csv"))
    rows = [r for r in rows if not (r["config_id"] == "60k" and r["position"] == "P3")]
    expect_failure("drop the 60k P3 row", "opt1_table1_per_position.csv", rows)

    rows = deepcopy(load("positions.csv"))
    a = next(r for r in rows if r["position"] == "P2")
    a["carrier_to_tag_cm"], a["tag_to_receiver_cm"] = a["tag_to_receiver_cm"], a["carrier_to_tag_cm"]
    expect_failure("swap the two distances of P2", "positions.csv", rows)

    print(f"self-test: {'PASS (every mutation detected)' if ok else 'FAIL (a mutation went undetected)'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--self-test", action="store_true", help="also run the mutation self-test")
    args = parser.parse_args()

    all_ok = True
    print("cell check: CSV values against the parsed table cells of the cited PDF pages")
    for name in SPECS:
        errs = cell_check(name, load(name))
        print(f"  {name}: {'OK' if not errs else f'{len(errs)} problem(s)'}")
        for e in errs:
            print(f"      {e}")
        all_ok = all_ok and not errs

    print("token check (weak): every value occurs somewhere on the cited page")
    total_checked = total_found = 0
    for name in SPECS:
        checked, found, missing = token_check(name, load(name))
        total_checked += checked
        total_found += found
        for m in missing:
            print(f"      MISSING {m}")
        all_ok = all_ok and not missing
    print(f"  values checked: {total_checked}, found on the cited page: {total_found}")

    if args.self_test:
        all_ok = self_test() and all_ok

    print("RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
