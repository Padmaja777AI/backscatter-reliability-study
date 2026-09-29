# Analysis scripts

These scripts **reproduce calculations and plots from the published report tables**.
They do not reproduce the original hardware experiments: the raw receiver logs, the
modified firmware and the receiver settings used in the laboratory are not part of
this repository (see [docs/provenance.md](../docs/provenance.md)).

| Script | Input | Output | Purpose |
|---|---|---|---|
| `summarize.py` | `data/reported/*.csv` | `analysis/output/*.csv`, `analysis/output/summary.md`, `analysis/output/transcribed_tables.md` | Re-applies the reports' own averaging method, computes unweighted means over the four common positions, ranks configurations per position, lists midpoint outcomes, runs an approximate packet-count consistency check, and compares Optimisation 2 with the baseline. |
| `plot.py` | `data/reported/*.csv`, `analysis/output/opt1_common_position_means.csv` | `docs/figures/generated/*.png` | Draws the four figures used in the documentation. Positions without reception are drawn as "no reception" markers, never as 100 % bars. |
| `verify_transcription.py` | `data/reported/*.csv`, `docs/reports/*.pdf` | console report, exit status | Checks that every transcribed value occurs on the cited page of the cited PDF. |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r analysis/requirements.txt
python3 analysis/summarize.py
python3 analysis/plot.py
python3 analysis/verify_transcription.py
```

Conventions the scripts rely on:

* `reception` in the CSVs is `received` or `none`. The reports' "BER = 100 %" entry
  for positions without reception is kept in `ber_reported_pct` as printed, while the
  normalised `ber_pct` column is empty there. Only the report's own Table 2 method
  (section 1 of `summary.md`) ever averages the 100 % marker, and it is labelled as
  sentinel-inclusive when it does.
* A data rate of 0 bytes/s at a position without reception is a legitimate
  throughput outcome and is kept as a number.
* All averages across positions are unweighted arithmetic means.
* The reports' effective data rate counts received payload bytes, including bytes
  that contain errors; it is not verified error-free goodput.
