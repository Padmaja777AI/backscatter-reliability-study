# Provenance

What every file in this repository is, where it came from, and how to verify that the
originals are unchanged. The machine-readable companions are
[`data/provenance/checksums.sha256`](../data/provenance/checksums.sha256) (SHA-256 of
every PDF and every vendored platform file, `sha256sum -c` format) and
[`data/provenance/source-archive-listing.txt`](../data/provenance/source-archive-listing.txt)
(the `unzip -l` listing of the university archive as provided).

## 1. Source material as provided

| Original file (as provided) | Bytes | SHA-256 | In this repository |
|---|---|---|---|
| `Group6_Experimental_optimisation_1.pdf` | 2,164,619 | `f1a486bed13976fbb7c697da5ae8c7b297dbb93cdb370e1013a3f4925d6c008a` | `docs/reports/Group6_Experimental_Optimisation_1_Baud_Rate.pdf` (renamed, bytes unchanged) |
| `Group6_Experimental_optimisation_2-3.pdf` | 2,122,941 | `766d60235f44a74dcb1e8ae00a67bcc6a0c84cca4e2a2cee67591db5061c5d26` | `docs/reports/Group6_Experimental_Optimisation_2_250kBaud_Longer_Packets.pdf` (renamed, bytes unchanged) |
| `Padmaja_analytical_optimisation (1).pdf` (uploaded as `Padmaja_analytical_optimisation_1.pdf`) | 146,356 | `2de5e427c9b21f5e2c8a343df898178435e1ff2ffd455392d124dda46e6d695f` | `docs/reports/Pabbathi_Analytical_Optimisation_FEC_Interleaving.pdf` (renamed, bytes unchanged) |
| `wcnes-project2026-main.zip` | 1,097,511 | `e23d54c1960fa11542832e15faa03613894e0b6df05697b297126c33224fd3b8` | unpacked to `platform/wcnes-project2026/` (65 of 66 files, bytes unchanged) |


Dates, recorded separately because they are different things:

| Report | Date printed on the title page | PDF metadata `CreationDate` / `ModDate` (as stored) | Pages | Producer |
|---|---|---|---|---|
| Optimisation 1 | May 2026 | `D:20260524213423Z` (both) | 7 | pdfTeX-1.40.27, LaTeX with hyperref |
| Optimisation 2 | May 2026 | `D:20260527105815Z` (both) | 6 | pdfTeX-1.40.27, LaTeX with hyperref |
| Analytical optimisation | June 2026 | `D:20260929082918Z` (both) | 4 | pdfTeX-1.40.27, LaTeX with hyperref |

The metadata date of the analytical report is later than its printed date. Why the file
carries that date is not documented; the repository owner supplied it as the final
submitted version.

## 2. University platform archive

* The archive is a snapshot of the course repository's `main` branch: its comment field
  carries the upstream commit id `8e1cc2b776cb677452c4f3d800d088d6a204a8af`, every entry
  carries the raw ZIP timestamp `2026-03-23 12:37` (the archive's own date/time field,
  which records no time zone), and the README changelog ends at 19.03.2026.
* All 66 files are listed in `data/provenance/source-archive-listing.txt`. 65 are
  vendored byte-for-byte (CRLF line endings preserved; see `.gitattributes`).
* **Deliberately omitted:** `hardware/fp-info-cache`, a KiCad footprint-info cache that
  KiCad regenerates on demand: 3,158,570 bytes, SHA-256
  `c53a7051737cfcf5334fbdb1dae70f8eaa3a5099a078b68a6c8712d9eb575011`. Nothing else was
  removed, renamed or edited.
* Authorship inside the archive: every C, Python and PIO source names Tobias Mages and
  Wenqing Yan; `stats/functions.py` carries "Copyright 2023, 2023 Wenqing Yan";
  `LICENSE.txt` is BSD 3-Clause, Copyright (c) 2023, Tobias Mages, Wenqing Yan.
* **Course reference data, not Group 6 measurements:** `stats/baseline_3m_c25.csv`,
  `baseline_3m_c50.csv`, `baseline_3m_rx25.csv`, `baseline_3m_rx50.csv` (200 packets
  each) and `stats/log.txt` (999 lines) ship with the platform (README changelog:
  "19.03.2026 … Added requirement.txt and baseline stats files"). Their values (for
  example 91.4 % bit reliability at 25 cm from the receiver) do not match Group 6's
  baseline table, and the notebook uses them as the radar-plot reference.
* The archive contains **no** Group 6 modifications: `DESIRED_BAUD` is 100000,
  `PAYLOADSIZE` is 14, `TX_DURATION` is 250, and no group logs or scripts are present.

## 3. Reports and photographs

* The three PDFs are stored unchanged (hashes above). They are the final submitted
  versions as provided by the repository owner.
* `docs/figures/report-photos/carrier-node-nrf52840.jpg` and
  `docs/figures/report-photos/tag-and-cc1352-receiver.jpg` are downscaled copies
  (750 × 1000 px JPEG) of the two 3840 × 5120 px photographs embedded on page 2 of the
  Optimisation 1 report (Figures 1 and 2); the same two image objects are embedded in
  the Optimisation 2 report (identical bytes: SHA-256 prefixes `5065e0dd86c6b4c7` and
  `61ac365dbc450ef1`). They are reproduced only to illustrate the setup.

## 4. Material created for this repository

| Path | What it is | How it was made |
|---|---|---|
| `data/reported/*.csv` | transcriptions of the published tables with report/page/table references, reception flags and notes | typed from the PDFs; checked cell by cell with `analysis/verify_transcription.py` against the tables parsed from the PDF text layer |
| `analysis/summarize.py`, `analysis/plot.py`, `analysis/verify_transcription.py` | new scripts | written for this repository; BSD 3-Clause |
| `analysis/output/*` | recomputed summaries | generated by `summarize.py` |
| `docs/figures/generated/*.png` | new figures | generated by `plot.py` from the CSVs; not the original report figures |
| `docs/*.md`, `README.md`, `NOTICE.md` | documentation | written for this repository from the reports and the platform code |

## 5. Not available, and therefore not in this repository

* The tag firmware Group 6 flashed for 80, 70, 60, 50 and 250 kBaud and for the longer
  packet, and the exact parameters changed (`DESIRED_BAUD` or generator arguments,
  `PAYLOADSIZE`, `TX_DURATION`, clock dividers).
* The SmartRF receiver settings for each configuration.
* The raw receiver logs of the 6 configurations × 5 positions (+ 2 extra baseline
  trials), the packet counts, and the run durations of the 250 kBaud runs.
* The scripts that produced the report figures and the PRR values.
* The LaTeX sources of the reports.

None of these have been reconstructed. Where documentation describes what a change
*would* touch in the platform code ([reproduction.md](reproduction.md)), it is labelled
as guidance written after the fact.

## 6. Verifying

```bash
sha256sum -c data/provenance/checksums.sha256      # every PDF and platform file
python3 analysis/verify_transcription.py --self-test  # CSV cells vs the parsed PDF tables
```

## 7. Tooling

The documentation, transcriptions, manifests and scripts were prepared with the
assistance of Claude Code (Anthropic) and reviewed by the repository owner. The
laboratory work, measurements and reports are the work of the people credited in
[NOTICE.md](../NOTICE.md); the reports keep their own statements, including the
analytical report's disclosure of AI assistance with language and structuring.
