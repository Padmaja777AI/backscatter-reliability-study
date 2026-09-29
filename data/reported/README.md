# Transcribed report tables

Faithful transcriptions of the numerical tables published in the Group 6 reports.
Every row cites the report file (`source_report`), the page (`source_page`) and the
table (`source_table`) it was copied from, so each value can be checked against the
PDF in [`docs/reports/`](../../docs/reports/). `analysis/verify_transcription.py`
performs that check automatically.

## Conventions

* Values are transcribed **as printed**, including the reports' failure markers
  ("BER = 100 %", "D/R = 0") for positions where no packets were received.
* `reception` states explicitly whether packets were received (`received` / `none`).
* `ber_pct` is a **normalised** bit error rate: equal to `ber_reported_pct` where
  packets were received and **empty** where none were, because a 100 % entry there is
  a failure marker rather than a measured bit-error ratio. Use `ber_pct` for
  statistics and `ber_reported_pct` only to reproduce the report's own tables.
* A blank cell corresponds to a dash in the report (no value printed).
* `note` records anything unusual about the printed value (for example a data rate
  printed as ".93", or two values that are not mutually consistent). Nothing has been
  corrected; see [docs/limitations-and-errata.md](../../docs/limitations-and-errata.md).

## Files

### `positions.csv`
Tag positions along the 3 m line between carrier generator and receiver
(Experimental Setup, page 2 of both experimental reports).

| column | meaning |
|---|---|
| `position` | P1 … P5 |
| `carrier_to_tag_cm`, `tag_to_receiver_cm` | distances in centimetres as listed in the reports |
| `description` | role of the position |

### `opt1_table1_per_position.csv`
Optimisation 1 (baud rate), Table 1, page 4: BER, effective data rate and run
duration for five baud rates at five positions.

| column | meaning |
|---|---|
| `config_id`, `baud_kbaud` | configuration (`100k` … `50k`) |
| `config_role` | `baseline` (100k) or `optimised` |
| `trials` | 3 for the baseline (values are averages of three trials), otherwise 1 |
| `reception` | `received` or `none` |
| `ber_reported_pct` | BER in % as printed (100.00 = failure marker) |
| `ber_pct` | normalised BER in %, empty when `reception` is `none` |
| `data_rate_reported_bytes_per_s` | effective data rate as printed; 0.00 where nothing was received |
| `duration_reported_s` | run duration in seconds as printed; empty where the report prints a dash |

### `opt1_table2_averages.csv`
Optimisation 1, Table 2, page 5: the report's own per-configuration averages, with
its stated averaging method. Kept so that `analysis/summarize.py` can compare its
re-computation against the published values.

### `opt2_table1_per_position.csv`
Optimisation 2 (250 kBaud with longer packets), Table 1, page 4: BER, effective
data rate and packet reception rate (PRR) for the baseline and the optimised
configuration. This table has no duration column. `prr_reported_pct` is kept exactly
as printed; the report's PRR definition is discussed in the errata.
