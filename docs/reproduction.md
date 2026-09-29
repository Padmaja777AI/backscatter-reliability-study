# Reproduction

Two different things can be reproduced, and it matters which one is meant.

## A. Recompute the tables and figures from the published report tables (done and tested here)

Requires Python 3.10+ and the packages in `analysis/requirements.txt`.

```bash
git clone https://github.com/Padmaja777AI/backscatter-reliability-study.git
cd backscatter-reliability-study
python3 -m venv .venv && source .venv/bin/activate
pip install -r analysis/requirements.txt

python3 analysis/summarize.py             # writes analysis/output/*.csv, summary.md, transcribed_tables.md
python3 analysis/plot.py                  # writes docs/figures/generated/*.png
python3 analysis/verify_transcription.py --self-test   # CSV cells vs the parsed PDF tables (needs pymupdf)
sha256sum -c data/provenance/checksums.sha256   # confirms the PDFs and platform files are unchanged
```

Expected results: `summarize.py` reproduces the reports' Table 2 to two decimals
(70 kBaud duration 105.29 vs 105.30 s, see the errata); `verify_transcription.py` prints
`RESULT: PASS`; `sha256sum -c` reports every file as OK.

What `verify_transcription.py` establishes. It parses each cited table from the PDF's
text layer (one printed row per text line; the configuration from the label printed in
the first column of the row group; the position from the P1–P5 token; the metric columns
in printed order) and compares every CSV cell by configuration, position and metric. It
also requires the exact expected set of rows, no duplicates, blanks only where the report
prints a dash, reception flags that match the report's failure marker, a normalised BER
equal to the printed BER on received rows, and correct report/page/table references.
`--self-test` swaps two different values on the same page, flips a reception flag,
alters a normalised BER, cites a wrong page, duplicates and drops rows, and confirms the
cell check fails on each. A supplementary page-token check is kept but is weak: it does
not notice a value in the wrong row or column, which the self-test also shows. Passing
means the CSVs match the tables as printed; it says nothing about whether the reports'
own values are correct.

Recorded environment in which the committed outputs were generated and found repeatable
(two consecutive runs produced byte-identical CSVs, markdown and PNGs): Python 3.11.15,
matplotlib 3.11.2, PyMuPDF 1.28.2, Linux x86_64 (glibc 2.39). Other matplotlib versions
may render the PNGs with small pixel differences.

This workflow only re-derives numbers from the tables. It does not touch hardware and it
cannot produce anything the reports do not contain.

## B. Re-run the hardware experiments (not performed for this repository)

The platform's own instructions are the authoritative guide:

* build and flash a tag: `platform/wcnes-project2026/README.md`,
  `platform/wcnes-project2026/carrier-receiver-baseband/README.md` (Pico SDK, CMake,
  `picotool`);
* carrier options: `carrier-nrf52840/`, `carrier-CC2500/`, `carrier-Firefly/`,
  `carrier-receiver-CC1352/`;
* receiver options: `carrier-receiver-CC1352/` (SmartRF Studio Packet RX; the sync word
  must match `packet_generation.c`), `receiver-CC2500/`;
* logging and evaluation: `carrier-receiver-baseband/serial-print.py`,
  `stats/statistics.ipynb` with `stats/functions.py`, expecting one line per packet in
  the form `timestamp | len seq payload | rssi`.

No firmware was compiled and no hardware was run while preparing this repository, so
the steps above are not verified here.

### Where a baud-rate or packet-length change lives in the platform code

This is guidance written after the fact for anyone repeating the Group 6 experiments.
**It is not the firmware Group 6 used**, which is not available.

| Change | Tag side | Receiver side | Analysis side |
|---|---|---|---|
| Baud rate | `DESIRED_BAUD` in `carrier-receiver-baseband/main.c` (run-time PIO), or the `baud-rate` argument of `baseband/generate-backscatter-pio.py` (compile-time PIO); the library snaps to the nearest rate that divides 125 MHz and recomputes centre offset, deviation and minimum RX bandwidth | CC2500: `set_datarate_rx`, `set_frequency_deviation_rx`, `set_filter_bandwidth_rx`, `set_frecuency_rx` from the returned `backscatter_config`; CC1352: data rate, deviation and RX filter BW in SmartRF | none |
| Packet length | `PAYLOADSIZE` in `project_pico_libs/packet_generation.h` (must stay even; length byte = 1 + `PAYLOADSIZE`; the CC2500 FIFO limits the payload to about 60 bytes) | CC1352 SmartRF length configuration (fixed or variable) | `PAYLOADSIZE` in the first cell of `stats/statistics.ipynb` |
| Transmit spacing | `TX_DURATION` (configured delay between packets; keep it longer than the transmission time) | none | none |
