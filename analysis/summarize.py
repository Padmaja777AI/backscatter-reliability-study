#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Padmaja Pabbathi
"""Recompute summary statistics from the transcribed report tables.

Inputs  : data/reported/*.csv  (faithful transcriptions of the published tables,
          including the report's "BER = 100 %" failure markers, with an explicit
          `reception` column and a normalised `ber_pct` that is empty when no
          packets were received)
Outputs : analysis/output/*.csv and analysis/output/summary.md

Everything produced here is a NEW calculation from published, rounded table
values.  The script reproduces calculations and plots from the reports; it does
not reproduce the original hardware experiments, and it cannot recover
information that the reports do not contain (raw logs, packet counts, radio
settings).  Averages across positions are unweighted.
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reported"
OUT = ROOT / "analysis" / "output"

POSITIONS = ["P1", "P2", "P3", "P4", "P5"]
COMMON = ["P1", "P2", "P4", "P5"]          # positions with reception in every Opt. 1 configuration
CONFIG_ORDER_OPT1 = ["100k", "80k", "70k", "60k", "50k"]
PAYLOAD_BYTES_IN_DR_FORMULA = 12          # L_payload used by the reports' D/R definition


def read_csv(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fnum(value: str) -> float | None:
    value = (value or "").strip()
    return float(value) if value else None


def write_csv(name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value, digits=2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def md_table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join("" if c is None else str(c) for c in row) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Optimisation 1                                                               #
# --------------------------------------------------------------------------- #
def opt1_rows() -> dict[str, dict[str, dict]]:
    table: dict[str, dict[str, dict]] = {}
    for row in read_csv("opt1_table1_per_position.csv"):
        table.setdefault(row["config_id"], {})[row["position"]] = {
            "reception": row["reception"],
            "ber_reported": fnum(row["ber_reported_pct"]),
            "ber": fnum(row["ber_pct"]),
            "dr": fnum(row["data_rate_reported_bytes_per_s"]),
            "duration": fnum(row["duration_reported_s"]),
            "trials": int(row["trials"]),
            "baud": int(row["baud_kbaud"]),
        }
    return table


def recompute_table2(table) -> tuple[list[dict], str]:
    """Re-apply the report's own Table 2 method to the Table 1 values."""
    reported = {r["config_id"]: r for r in read_csv("opt1_table2_averages.csv")}
    rows = []
    for cfg in CONFIG_ORDER_OPT1:
        cells = table[cfg]
        avg_ber_sentinel = statistics.mean(c["ber_reported"] for c in cells.values())
        avg_dr = statistics.mean(c["dr"] for c in cells.values())
        durations = [c["duration"] for c in cells.values() if c["duration"] is not None]
        avg_duration = statistics.mean(durations)
        rep = reported[cfg]
        rows.append({
            "config_id": cfg,
            "avg_ber_sentinel_inclusive_pct_recomputed": round(avg_ber_sentinel, 3),
            "avg_ber_reported_pct_table2": fnum(rep["avg_ber_reported_pct"]),
            "avg_ber_difference": round(avg_ber_sentinel - fnum(rep["avg_ber_reported_pct"]), 3),
            "avg_data_rate_bytes_per_s_recomputed": round(avg_dr, 3),
            "avg_data_rate_reported_table2": fnum(rep["avg_data_rate_reported_bytes_per_s"]),
            "avg_data_rate_difference": round(avg_dr - fnum(rep["avg_data_rate_reported_bytes_per_s"]), 3),
            "avg_duration_s_recomputed": round(avg_duration, 3),
            "n_positions_in_duration_average": len(durations),
            "avg_duration_reported_table2": fnum(rep["avg_duration_reported_s"]),
            "avg_duration_difference": round(avg_duration - fnum(rep["avg_duration_reported_s"]), 3),
        })
    write_csv("opt1_table2_recomputed.csv", rows)
    md = md_table(
        ["Config", "Avg BER % (sentinel-inclusive), recomputed", "Table 2", "Avg D/R bytes/s, recomputed", "Table 2",
         "Avg duration s, recomputed", "n positions", "Table 2"],
        [[r["config_id"], fmt(r["avg_ber_sentinel_inclusive_pct_recomputed"]), fmt(r["avg_ber_reported_pct_table2"]),
          fmt(r["avg_data_rate_bytes_per_s_recomputed"]), fmt(r["avg_data_rate_reported_table2"]),
          fmt(r["avg_duration_s_recomputed"]), r["n_positions_in_duration_average"], fmt(r["avg_duration_reported_table2"])]
         for r in rows],
    )
    return rows, md


def common_position_means(table) -> tuple[list[dict], str]:
    rows = []
    for cfg in CONFIG_ORDER_OPT1:
        cells = [table[cfg][p] for p in COMMON]
        assert all(c["reception"] == "received" for c in cells), cfg
        rows.append({
            "config_id": cfg,
            "baud_kbaud": cells[0]["baud"],
            "positions": "P1;P2;P4;P5",
            "n_positions": len(cells),
            "trials_per_position": cells[0]["trials"],
            "mean_ber_pct": round(statistics.mean(c["ber"] for c in cells), 3),
            "min_ber_pct": min(c["ber"] for c in cells),
            "max_ber_pct": max(c["ber"] for c in cells),
            "mean_data_rate_bytes_per_s": round(statistics.mean(c["dr"] for c in cells), 3),
            "mean_duration_s": round(statistics.mean(c["duration"] for c in cells), 3),
        })
    write_csv("opt1_common_position_means.csv", rows)
    md = md_table(
        ["Config", "Trials / position", "Mean BER % (P1,P2,P4,P5)", "BER range %", "Mean D/R bytes/s", "Mean duration s"],
        [[r["config_id"], r["trials_per_position"], fmt(r["mean_ber_pct"]),
          f"{fmt(r['min_ber_pct'])}–{fmt(r['max_ber_pct'])}", fmt(r["mean_data_rate_bytes_per_s"]), fmt(r["mean_duration_s"])]
         for r in rows],
    )
    return rows, md


def per_position(table) -> tuple[list[dict], list[dict], str]:
    long_rows, winner_rows = [], []
    for pos in POSITIONS:
        received = {cfg: table[cfg][pos] for cfg in CONFIG_ORDER_OPT1 if table[cfg][pos]["reception"] == "received"}
        by_ber = sorted(received, key=lambda c: received[c]["ber"])
        by_dr = sorted(received, key=lambda c: -received[c]["dr"])
        by_dur = sorted(received, key=lambda c: received[c]["duration"])
        for cfg in CONFIG_ORDER_OPT1:
            cell = table[cfg][pos]
            long_rows.append({
                "position": pos,
                "config_id": cfg,
                "reception": cell["reception"],
                "ber_pct": cell["ber"],
                "data_rate_bytes_per_s": cell["dr"],
                "duration_s": cell["duration"],
                "rank_lowest_ber": by_ber.index(cfg) + 1 if cfg in received else "",
                "rank_highest_data_rate": by_dr.index(cfg) + 1 if cfg in received else "",
                "rank_shortest_duration": by_dur.index(cfg) + 1 if cfg in received else "",
            })
        winner_rows.append({
            "position": pos,
            "n_configs_with_reception": len(received),
            "lowest_ber_config": by_ber[0], "lowest_ber_pct": received[by_ber[0]]["ber"],
            "second_lowest_ber_config": by_ber[1] if len(by_ber) > 1 else "",
            "second_lowest_ber_pct": received[by_ber[1]]["ber"] if len(by_ber) > 1 else "",
            "highest_data_rate_config": by_dr[0], "highest_data_rate_bytes_per_s": received[by_dr[0]]["dr"],
            "shortest_duration_config": by_dur[0], "shortest_duration_s": received[by_dur[0]]["duration"],
        })
    write_csv("opt1_per_position_ranking.csv", long_rows)
    write_csv("opt1_per_position_winners.csv", winner_rows)
    md = md_table(
        ["Position", "Configs with reception", "Lowest BER", "Runner-up", "Highest D/R", "Shortest duration"],
        [[w["position"], w["n_configs_with_reception"],
          f"{w['lowest_ber_config']} ({fmt(w['lowest_ber_pct'])} %)",
          f"{w['second_lowest_ber_config']} ({fmt(w['second_lowest_ber_pct'])} %)" if w["second_lowest_ber_config"] else "—",
          f"{w['highest_data_rate_config']} ({fmt(w['highest_data_rate_bytes_per_s'])} bytes/s)",
          f"{w['shortest_duration_config']} ({fmt(w['shortest_duration_s'])} s)"] for w in winner_rows],
    )
    return long_rows, winner_rows, md


def midpoint(table) -> tuple[list[dict], str]:
    rows = []
    for cfg in CONFIG_ORDER_OPT1:
        cell = table[cfg]["P3"]
        rows.append({
            "config_id": cfg,
            "reception": cell["reception"],
            "ber_pct": cell["ber"] if cell["reception"] == "received" else "",
            "data_rate_bytes_per_s": cell["dr"],
            "duration_s": cell["duration"] if cell["duration"] is not None else "",
            "outcome": ("packets received" if cell["reception"] == "received"
                        else "no packets received within the 5-minute cap (report marker: BER = 100 %, D/R = 0)"),
        })
    write_csv("opt1_midpoint_outcomes.csv", rows)
    md = md_table(
        ["Config", "Midpoint P3 outcome", "BER %", "D/R bytes/s", "Duration s"],
        [[r["config_id"], r["outcome"], fmt(r["ber_pct"]) if r["ber_pct"] != "" else "not measurable",
          fmt(r["data_rate_bytes_per_s"]), fmt(r["duration_s"]) if r["duration_s"] != "" else "—"] for r in rows],
    )
    return rows, md


def packet_count_check(table) -> tuple[list[dict], str]:
    rows = []
    for cfg in CONFIG_ORDER_OPT1:
        for pos in POSITIONS:
            cell = table[cfg][pos]
            if cell["reception"] != "received":
                continue
            implied = cell["dr"] * cell["duration"] / PAYLOAD_BYTES_IN_DR_FORMULA
            rows.append({
                "config_id": cfg, "position": pos,
                "implied_packets_dr_times_duration_over_12B": round(implied, 1),
                "caveat": ("baseline: product of two separately averaged trial means; approximate only"
                           if cell["trials"] > 1 else "approximate consistency check from rounded published values"),
            })
    write_csv("opt1_implied_packet_count_check.csv", rows)
    vals = [r["implied_packets_dr_times_duration_over_12B"] for r in rows]
    md = (f"Across the {len(rows)} cells with reception, D/R × duration / 12 bytes lies between "
          f"{min(vals):.1f} and {max(vals):.1f}. This only checks that the published D/R, duration and the "
          f"12-byte payload definition are mutually consistent with the stated 'about 200 packets' protocol; "
          f"it is not an exact packet count, and for the baseline it multiplies two separately averaged means.")
    return rows, md


# --------------------------------------------------------------------------- #
# Optimisation 2                                                               #
# --------------------------------------------------------------------------- #
def opt2_comparison() -> tuple[list[dict], str]:
    data: dict[str, dict[str, dict]] = {}
    for row in read_csv("opt2_table1_per_position.csv"):
        data.setdefault(row["config_id"], {})[row["position"]] = {
            "reception": row["reception"], "ber": fnum(row["ber_pct"]),
            "dr": fnum(row["data_rate_reported_bytes_per_s"]), "prr": fnum(row["prr_reported_pct"]),
            "note": row["note"],
        }
    rows = []
    for pos in POSITIONS:
        b, o = data["100k"][pos], data["250k_long"][pos]
        both = b["reception"] == "received" and o["reception"] == "received"
        implied = (o["prr"] / 100.0 * PAYLOAD_BYTES_IN_DR_FORMULA / o["dr"]) if (o["prr"] is not None and o["dr"]) else None
        implied_b = (b["prr"] / 100.0 * PAYLOAD_BYTES_IN_DR_FORMULA / b["dr"]) if (b["prr"] is not None and b["dr"]) else None
        rows.append({
            "position": pos,
            "baseline_reception": b["reception"], "baseline_ber_pct": b["ber"], "baseline_data_rate_bytes_per_s": b["dr"],
            "baseline_prr_pct": b["prr"],
            "opt2_reception": o["reception"], "opt2_ber_pct": o["ber"], "opt2_data_rate_bytes_per_s": o["dr"],
            "opt2_prr_pct": o["prr"],
            "ber_change_pct_points": round(o["ber"] - b["ber"], 2) if both else "",
            "ber_ratio_opt2_over_baseline": round(o["ber"] / b["ber"], 2) if both else "",
            "data_rate_change_bytes_per_s": round(o["dr"] - b["dr"], 2) if both else "",
            "prr_change_pct_points": round(o["prr"] - b["prr"], 1) if (both and o["prr"] is not None and b["prr"] is not None) else "",
            "diagnostic_baseline_prr_pct_x_12B_over_dr_s": round(implied_b, 3) if implied_b is not None else "",
            "diagnostic_opt2_prr_pct_x_12B_over_dr_s": round(implied, 3) if implied is not None else "",
            "note": o["note"],
        })
    write_csv("opt2_baseline_vs_250k_comparison.csv", rows)
    md = md_table(
        ["Position", "Baseline BER %", "250k BER %", "BER ratio", "Baseline D/R", "250k D/R", "Baseline PRR %", "250k PRR %"],
        [[r["position"],
          fmt(r["baseline_ber_pct"]) if r["baseline_reception"] == "received" else "no reception",
          fmt(r["opt2_ber_pct"], 1) if r["opt2_reception"] == "received" else "no reception",
          fmt(r["ber_ratio_opt2_over_baseline"]) if r["ber_ratio_opt2_over_baseline"] != "" else "—",
          fmt(r["baseline_data_rate_bytes_per_s"]), fmt(r["opt2_data_rate_bytes_per_s"]),
          fmt(r["baseline_prr_pct"], 1) if r["baseline_prr_pct"] is not None else "—",
          fmt(r["opt2_prr_pct"], 1) if r["opt2_prr_pct"] is not None else "—"] for r in rows],
    )
    return rows, md


def transcribed_tables_md() -> str:
    """Render the CSV transcriptions as markdown (as printed, with reception status)."""
    t1 = read_csv("opt1_table1_per_position.csv")
    t2 = read_csv("opt1_table2_averages.csv")
    o2 = read_csv("opt2_table1_per_position.csv")
    src = lambda r: f"{r['source_report']} p. {r['source_page']}, {r['source_table']}"
    a = md_table(["Config", "Trials", "Position", "Reception", "BER % as printed", "D/R bytes/s as printed", "Duration s as printed"],
                 [[r["config_id"], r["trials"], r["position"], r["reception"], r["ber_reported_pct"],
                   r["data_rate_reported_bytes_per_s"], r["duration_reported_s"] or "—"] for r in t1])
    b = md_table(["Config", "Avg BER % as printed", "Avg D/R bytes/s as printed", "Avg duration s as printed"],
                 [[r["config_id"], r["avg_ber_reported_pct"], r["avg_data_rate_reported_bytes_per_s"],
                   r["avg_duration_reported_s"]] for r in t2])
    c = md_table(["Config", "Trials", "Position", "Reception", "BER % as printed", "D/R bytes/s as printed", "PRR % as printed"],
                 [[r["config_label_as_printed"], r["trials"], r["position"], r["reception"], r["ber_reported_pct"],
                   r["data_rate_reported_bytes_per_s"], r["prr_reported_pct"] or "—"] for r in o2])
    return f"""# Transcribed report tables (as printed)

Generated by `analysis/summarize.py` from `data/reported/*.csv`. Values are exactly as
printed in the reports; "100.00" BER with reception `none` is the reports' failure
marker for "no packets received", not a measured bit-error ratio.

## Optimisation 1, Table 1 ({src(t1[0])})

{a}

## Optimisation 1, Table 2 ({src(t2[0])})

{b}

Stated method: BER and D/R averaged over all five positions with P3 failures entered as
BER = 100 % and D/R = 0; duration averaged only over positions where packets were received.

## Optimisation 2, Table 1 ({src(o2[0])})

{c}

Notes recorded during transcription: the P2 data rate of the 250k configuration is
printed as ".93"; the P4 pair (11.2 bytes/s, 1 %) is preserved although it is not
self-consistent under the report's definitions; the table has no duration column.
"""


def main() -> None:
    table = opt1_rows()
    t2_rows, t2_md = recompute_table2(table)
    cm_rows, cm_md = common_position_means(table)
    _, winners, pp_md = per_position(table)
    mp_rows, mp_md = midpoint(table)
    _, pc_md = packet_count_check(table)
    o2_rows, o2_md = opt2_comparison()

    best_common = min(cm_rows, key=lambda r: r["mean_ber_pct"])
    fastest = min(cm_rows, key=lambda r: r["mean_duration_s"])
    t70 = next(r for r in t2_rows if r["config_id"] == "70k")
    p1 = next(r for r in o2_rows if r["position"] == "P1")

    text = f"""# Summary tables recomputed from the published report tables

Generated by `analysis/summarize.py` from the CSV transcriptions in `data/reported/`.
Every number below is a **new calculation from published, rounded table values**; the
transcriptions cite the report, page and table they come from. Nothing here re-runs
the hardware experiments. Single-trial caveat: every configuration except the 100k
baseline (mean of three trials) was measured once, so small differences between
configurations are not statistically established.

## 1. Optimisation 1, Table 2 re-applied to Table 1

The report's Table 2 averages BER and D/R over all five positions **with the
"BER = 100 %, D/R = 0" failure marker entered for positions without reception**
("sentinel-inclusive"), and averages duration only over positions with reception.
Re-applying that method to the published Table 1 values gives:

{t2_md}

All values agree with the report's Table 2 to two decimals except the 70k mean
duration, where the published Table 1 values give {fmt(t70['avg_duration_s_recomputed'])} s against
{fmt(t70['avg_duration_reported_table2'])} s in Table 2 (difference {t70['avg_duration_difference']:+.3f} s). The cause of the
small discrepancy is not established from the published material (rounding of the
per-position values before averaging is one possibility). Note that the 70k duration
average covers five positions while the other four cover four, so that column is not
like-for-like across configurations.

The sentinel-inclusive BER average mixes measured bit-error ratios with an artificial
100 % marker and should not be read as a bit-error ratio. The D/R average is different in
kind: a data rate of 0 bytes/s at a position without reception is a legitimate
throughput outcome, so the D/R average does reflect coverage.

## 2. Unweighted means over the four common positions (P1, P2, P4, P5)

These are the positions where **every** configuration received packets, so no failure
marker enters the average. Unweighted arithmetic means across the four positions:

{cm_md}

Lowest mean BER over the common positions: **{best_common['config_id']}** ({fmt(best_common['mean_ber_pct'])} %).
Shortest mean duration over the common positions: **{fastest['config_id']}** ({fmt(fastest['mean_duration_s'])} s).

## 3. Best configuration at each individual position

{pp_md}

The configuration with the best common-position average is not the best at every
position: rankings differ between the carrier-side (P1, P2) and receiver-side (P4, P5)
positions.

## 4. Midpoint (P3) outcomes

{mp_md}

The 70k midpoint reception is a genuine coverage result: it is the only configuration
that delivered packets at the worst-case position, with a BER of about 30 % and a
run of 204.53 s. The other configurations' P3 entries are failure markers, not
measurements.

## 5. Consistency check: implied packet counts (approximate)

{pc_md}

## 6. Optimisation 2: 100k baseline versus 250k with longer packets

{o2_md}

At P1 the 250k data rate ({fmt(p1['opt2_data_rate_bytes_per_s'])} bytes/s) is close to but lower than the
baseline ({fmt(p1['baseline_data_rate_bytes_per_s'])} bytes/s). BER rose at every position with reception, by a factor of {', '.join(fmt(r['ber_ratio_opt2_over_baseline']) for r in o2_rows if r['ber_ratio_opt2_over_baseline'] != '')} at {', '.join(r['position'] for r in o2_rows if r['ber_ratio_opt2_over_baseline'] != '')} respectively; P3 and P5 received nothing.
The PRR values are preserved as printed. Two diagnostic columns in
`opt2_baseline_vs_250k_comparison.csv` compute PRR/100 × 12 bytes ÷ D/R, which under
the report's stated quantities equals the implied inter-packet interval **if** PRR is
read as expected time ÷ actual time and a 12-byte payload entered the D/R formula. It
is about 0.26 s for every baseline row and for 250k P2, about 0.20 s for 250k P1, and
about 0.01 s for 250k P4; the P4 pair is therefore not self-consistent under those
readings. The report does not state the payload length used in D/R for the 250k
configuration, and no on-air packet interval is documented, so these are diagnostics,
not corrections.
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    (OUT / "transcribed_tables.md").write_text(transcribed_tables_md(), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
