#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Padmaja Pabbathi
"""Generate figures from the transcribed report tables.

Inputs  : data/reported/*.csv
Outputs : docs/figures/generated/*.png

The figures are NEWLY GENERATED from the published tables of the Group 6 reports;
they are not the original report figures and they do not re-run the experiments.
Positions without reception are drawn as "no reception" markers, never as a
100 % bar, because the report's "BER = 100 %" entry is a failure marker.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reported"
OUT = ROOT / "docs" / "figures" / "generated"

# Chart chrome (light surface) and series colours.  The four optimised baud rates use
# one ordered blue ramp (lighter = lower baud rate); the baseline is a neutral grey.
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
REF = "#8f8e88"
BLUE, ORANGE = "#2a78d6", "#eb6834"
RAMP = {"50k": "#86b6ef", "60k": "#5598e7", "70k": "#2a78d6", "80k": "#104281", "100k": REF}
LABEL = {"50k": "50 kBaud", "60k": "60 kBaud", "70k": "70 kBaud", "80k": "80 kBaud",
         "100k": "100 kBaud baseline (mean of 3 trials)"}
SERIES = ["50k", "60k", "70k", "80k", "100k"]
POSITIONS = ["P1", "P2", "P3", "P4", "P5"]
FOOT = ("Newly generated from the published tables of the Group 6 reports (May 2026); not an original report "
        "figure. One trial per configuration except the 100 kBaud baseline.")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "legend.frameon": False,
})


def read(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fnum(v: str):
    v = (v or "").strip()
    return float(v) if v else None


def positions_labels() -> dict[str, str]:
    return {r["position"]: f"{r['position']}\n{r['carrier_to_tag_cm']}/{r['tag_to_receiver_cm']} cm"
            for r in read("positions.csv")}


def opt1_table():
    t: dict[str, dict[str, dict]] = {}
    for r in read("opt1_table1_per_position.csv"):
        t.setdefault(r["config_id"], {})[r["position"]] = {
            "rx": r["reception"] == "received", "ber": fnum(r["ber_pct"]),
            "dr": fnum(r["data_rate_reported_bytes_per_s"]), "dur": fnum(r["duration_reported_s"]),
        }
    return t


def style_axis(ax):
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)


def grouped_bars(ax, table, metric, ylabel, best):
    """Grouped bars per position; missing reception drawn as a marker, not a bar."""
    xt = positions_labels()
    n = len(SERIES)
    width, step = 0.14, 0.16
    for j, cfg in enumerate(SERIES):
        xs = [i + (j - (n - 1) / 2) * step for i in range(len(POSITIONS))]
        vals = [table[cfg][p][metric] if table[cfg][p]["rx"] else None for p in POSITIONS]
        ax.bar([x for x, v in zip(xs, vals) if v is not None], [v for v in vals if v is not None],
               width=width, color=RAMP[cfg], label=LABEL[cfg], zorder=3)
        for x, v in zip(xs, vals):
            if v is None:
                ax.plot(x, 0, marker="x", color=MUTED, markersize=6, markeredgewidth=1.2, zorder=4, clip_on=False)
    # selective direct labels: the best value at each position
    for i, p in enumerate(POSITIONS):
        cand = {cfg: table[cfg][p][metric] for cfg in SERIES if table[cfg][p]["rx"]}
        if not cand:
            continue
        cfg = best(cand)
        j = SERIES.index(cfg)
        x = i + (j - (n - 1) / 2) * step
        ax.annotate(f"{cand[cfg]:.2f}", (x, cand[cfg]), xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(range(len(POSITIONS)))
    ax.set_xticklabels([xt[p] for p in POSITIONS])
    ax.set_xlabel("Tag position (carrier-to-tag / tag-to-receiver distance)")
    ax.set_ylabel(ylabel)
    style_axis(ax)


def fig_opt1_ber():
    t = opt1_table()
    fig, ax = plt.subplots(figsize=(11, 5.6))
    grouped_bars(ax, t, "ber", "Bit error rate over received packets (%)", best=lambda c: min(c, key=c.get))
    ax.set_ylim(0, 38)
    ax.set_title("Optimisation 1: BER per tag position and baud rate", loc="left", fontsize=13, pad=14)
    ax.annotate("At P3 only 70 kBaud received packets;\n× = no reception within 5 min (report marker: BER = 100 %)",
                xy=(2.55, 32.5), ha="center", va="bottom", fontsize=8.5, color=INK2,
                bbox=dict(boxstyle="round,pad=0.35", fc=SURFACE, ec=GRID))
    handles = [Patch(color=RAMP[c], label=LABEL[c]) for c in SERIES] + \
              [Line2D([0], [0], marker="x", color=MUTED, linestyle="none", markersize=6, label="no reception")]
    ax.legend(handles=handles, loc="upper left", ncol=2, fontsize=8.5)
    fig.text(0.01, 0.01, FOOT, fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "opt1_ber_by_position.png", dpi=160)
    plt.close(fig)


def fig_opt1_dr():
    t = opt1_table()
    fig, ax = plt.subplots(figsize=(11, 5.6))
    grouped_bars(ax, t, "dr", "Effective data rate, received payload bytes per second", best=lambda c: max(c, key=c.get))
    ax.set_ylim(0, 50)
    ax.set_title("Optimisation 1: effective data rate per tag position and baud rate", loc="left", fontsize=13, pad=14)
    ax.annotate("D/R = received packets × 12 payload bytes ÷ run duration (report definition);\n"
                "counts received bytes, not verified error-free bytes. × = no reception (0 bytes/s)",
                xy=(2.75, 43), ha="center", va="bottom", fontsize=8.5, color=INK2,
                bbox=dict(boxstyle="round,pad=0.35", fc=SURFACE, ec=GRID))
    handles = [Patch(color=RAMP[c], label=LABEL[c]) for c in SERIES] + \
              [Line2D([0], [0], marker="x", color=MUTED, linestyle="none", markersize=6, label="no reception")]
    ax.legend(handles=handles, loc="upper left", ncol=2, fontsize=8.5)
    fig.text(0.01, 0.01, FOOT, fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "opt1_data_rate_by_position.png", dpi=160)
    plt.close(fig)


def fig_opt1_common_means():
    rows = {r["config_id"]: r for r in read_output("opt1_common_position_means.csv")}
    order = ["50k", "60k", "70k", "80k", "100k"]
    x = [int(rows[c]["baud_kbaud"]) for c in order]
    panels = [("mean_ber_pct", "Mean BER (%)", "lower is better", min),
              ("mean_data_rate_bytes_per_s", "Mean data rate (bytes/s)", "higher is better", max),
              ("mean_duration_s", "Mean run duration for ~200 packets (s)", "lower is better", min)]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, (key, ylabel, hint, pick) in zip(axes, panels):
        y = [float(rows[c][key]) for c in order]
        ax.plot(x, y, color=BLUE, linewidth=2, zorder=3)
        ax.plot(x[:-1], y[:-1], linestyle="none", marker="o", markersize=8, color=BLUE,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
        ax.plot(x[-1:], y[-1:], linestyle="none", marker="o", markersize=8, color=REF,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
        best_i = y.index(pick(y))
        ax.annotate(f"{y[best_i]:.2f}", (x[best_i], y[best_i]), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8.5, color=INK2)
        rising = y[-1] >= y[-2]  # keep the baseline label off the line segment that leads into the point
        ax.annotate(f"baseline {y[-1]:.2f}", (x[-1], y[-1]), xytext=(6, 9 if rising else -16),
                    textcoords="offset points", ha="right", fontsize=8.5, color=INK2)
        ax.set_xticks(x)
        ax.set_xlabel("Baud rate (kBaud)")
        ax.set_ylabel(ylabel)
        ax.set_title(hint, loc="left", fontsize=9, color=INK2)
        ax.set_ylim(0, max(y) * 1.25)
        style_axis(ax)
    fig.suptitle("Optimisation 1: unweighted means over the four common positions P1, P2, P4, P5\n"
                 "(the positions where every configuration received packets)", x=0.01, ha="left", fontsize=12)
    fig.text(0.01, 0.01, FOOT + " Grey point = 100 kBaud baseline.", fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    fig.savefig(OUT / "opt1_common_position_means.png", dpi=160)
    plt.close(fig)


def read_output(name: str) -> list[dict]:
    path = ROOT / "analysis" / "output" / name
    if not path.exists():
        raise SystemExit(f"{path} missing: run analysis/summarize.py first")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fig_opt2():
    t: dict[str, dict[str, dict]] = {}
    for r in read("opt2_table1_per_position.csv"):
        t.setdefault(r["config_id"], {})[r["position"]] = {
            "rx": r["reception"] == "received", "ber": fnum(r["ber_pct"]),
            "dr": fnum(r["data_rate_reported_bytes_per_s"]), "prr": fnum(r["prr_reported_pct"]),
        }
    xt = positions_labels()
    series = [("100k", REF, "100 kBaud baseline (mean of 3 trials)"), ("250k_long", BLUE, "250 kBaud + longer packets")]
    panels = [("ber", "BER over received packets (%)", 48), ("dr", "Effective data rate (bytes/s)", 38),
              ("prr", "Packet reception rate as reported (%)", 82)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.0))
    width, step = 0.3, 0.34
    for ax, (key, ylabel, ymax) in zip(axes, panels):
        for j, (cfg, colour, label) in enumerate(series):
            xs = [i + (j - 0.5) * step for i in range(len(POSITIONS))]
            vals = [t[cfg][p][key] if t[cfg][p]["rx"] else None for p in POSITIONS]
            ax.bar([x for x, v in zip(xs, vals) if v is not None], [v for v in vals if v is not None],
                   width=width, color=colour, label=label, zorder=3)
            for x, v, p in zip(xs, vals, POSITIONS):
                if v is None:
                    ax.plot(x, 0, marker="x", color=MUTED, markersize=6, markeredgewidth=1.2, zorder=4, clip_on=False)
                elif cfg == "250k_long":
                    txt = f"{v:.2f}" if key == "dr" else f"{v:.1f}"
                    ax.annotate(txt, (x, v), xytext=(0, 3), textcoords="offset points", ha="center",
                                va="bottom", fontsize=8.5, color=INK2)
        ax.set_xticks(range(len(POSITIONS)))
        ax.set_xticklabels([xt[p] for p in POSITIONS], fontsize=8.5)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, ymax)
        style_axis(ax)
    fig.legend(handles=[Patch(color=c, label=l) for _, c, l in series] +
               [Line2D([0], [0], marker="x", color=MUTED, linestyle="none", markersize=6, label="no reception")],
               loc="upper left", bbox_to_anchor=(0.01, 0.92), ncol=3, fontsize=9)
    fig.suptitle("Optimisation 2: 250 kBaud with longer packets versus the 100 kBaud baseline, per tag position",
                 x=0.01, ha="left", fontsize=12)
    fig.text(0.01, 0.01, FOOT + " PRR values are shown exactly as printed in the report (see errata).",
             fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    fig.savefig(OUT / "opt2_baseline_vs_250k.png", dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_opt1_ber()
    fig_opt1_dr()
    fig_opt1_common_means()
    fig_opt2()
    for p in sorted(OUT.glob("*.png")):
        print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
