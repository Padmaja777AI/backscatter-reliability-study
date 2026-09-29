# Notice: ownership, licences and provenance

This repository combines material from three sources. Each keeps its own ownership
and licence; nothing here re-licenses somebody else's work.

## 1. University platform (`platform/wcnes-project2026/`)

The Pico-Backscatter teaching platform of the course *Wireless Communication and
Networked Embedded Systems* (Uppsala University) is reproduced exactly as it was
provided to the students (archive `wcnes-project2026-main.zip`, see
[docs/provenance.md](docs/provenance.md)).

* Licence: BSD 3-Clause, **Copyright (c) 2023, Tobias Mages, Wenqing Yan**, in
  [`platform/wcnes-project2026/LICENSE.txt`](platform/wcnes-project2026/LICENSE.txt),
  unchanged.
* All author notices inside the source files (Tobias Mages & Wenqing Yan; the
  `stats/functions.py` header "Copyright 2023, 2023 Wenqing Yan") are unchanged.
* The only file deliberately left out is the generated KiCad cache
  `hardware/fp-info-cache` (3,158,570 bytes); its checksum is recorded in
  [docs/provenance.md](docs/provenance.md).
* The files `stats/baseline_3m_*.csv` and `stats/log.txt` are **course reference
  data shipped with the platform**, not measurements made by Group 6.
* Nothing in this repository is published or endorsed by Uppsala University or by
  the platform authors. Their names are used only to give credit, as the BSD
  licence requires.

## 2. Course reports (`docs/reports/`)

Three PDF reports are reproduced exactly as submitted, with their original
authorship, statements and AI-use declarations intact:

| File | Authors |
|---|---|
| `Group6_Experimental_Optimisation_1_Baud_Rate.pdf` | Group 6: Hardik Sai, Luke Nasby, Padmaja Pabbathi |
| `Group6_Experimental_Optimisation_2_250kBaud_Longer_Packets.pdf` | Group 6: Hardik Sai, Luke Nasby, Padmaja Pabbathi |
| `Pabbathi_Analytical_Optimisation_FEC_Interleaving.pdf` | Padmaja Pabbathi (individual submission) |

The reports are the copyright of their authors. **No new licence is applied to
them by this repository**; they are included here by a co-author for portfolio
and documentation purposes. The two photographs under
`docs/figures/report-photos/` are downscaled copies of the photographs embedded in
the Group 6 reports and are covered by the same statement.

## 3. New material for this repository

The following were created for this repository and are licensed under the
BSD 3-Clause licence in [LICENSE](LICENSE), **Copyright (c) 2026 Padmaja Pabbathi**:

* `README.md`, `NOTICE.md`, and the documentation under `docs/` (except
  `docs/reports/` and `docs/figures/report-photos/`);
* the CSV transcriptions under `data/reported/` (the numbers themselves are facts
  published in the reports; the transcription files, column conventions and notes
  are new);
* the provenance manifests under `data/provenance/`;
* the scripts under `analysis/`, their outputs under `analysis/output/`, and the
  figures under `docs/figures/generated/`.

## Tooling disclosure

The repository documentation, the CSV transcriptions, the provenance manifests and
the analysis and plotting scripts were prepared with the assistance of Claude Code
(Anthropic), working from the reports and the platform archive, and were reviewed
by the repository owner. The laboratory work, the measurements, the reports and the
analytical proposal are the work of the people credited above; no part of that
work was performed by an AI tool.
