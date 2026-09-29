# Experiments

Two experimental optimisations were carried out by Group 6 (Hardik Sai, Luke Nasby,
Padmaja Pabbathi) in the course laboratory in May 2026. Everything on this page is taken
from the two reports in [`reports/`](reports/); the report pages are cited so that each
statement can be checked. Where the reports are silent, this page says so rather than
filling the gap.

## 1. Common setup (both reports, page 2)

* Carrier generator and receiver about **3 m apart**; the tag placed at five positions on
  the straight line between them.
* Carrier: nRF52840 board in a plastic enclosure (Figure 1 of the reports). Receiver:
  CC1352 LaunchPad with SmartRF Studio on a laptop (Figure 2). Tag: the course PCB with
  two antennas, driven by a Raspberry Pi Pico.

| Position | Carrier → tag | Tag → receiver | Role |
|---|---|---|---|
| P1 | 27 cm | 273 cm | edge, nearest the carrier |
| P2 | 50 cm | 250 cm | carrier side |
| P3 | 150 cm | 150 cm | **midpoint, worst case** (both links at maximum path loss) |
| P4 | 250 cm | 50 cm | receiver side |
| P5 | 277 cm | 23 cm | edge, nearest the receiver |

* Protocol: the tag transmits continuously; the receiver logs packets **until 200 packets
  have been received**. The run duration is `Δt = t_last − t_first` over the received
  packets.
* At the midpoint the run was capped at **5 minutes**; if nothing was received the
  configuration was recorded as a communication failure with **"BER = 100 %" and
  "D/R = 0 byte/s"**. The 100 % entry is a failure marker, not a measured bit-error
  ratio; the 0 byte/s entry is a genuine throughput outcome. This repository keeps both
  as printed and adds an explicit reception flag (see
  [`data/reported/README.md`](../data/reported/README.md)).

## 2. Metrics (both reports, page 3)

| Metric | Definition in the reports | Notes |
|---|---|---|
| BER | wrong bits ÷ received bits, over received packets only | lost packets do not enter the BER |
| Effective data rate D/R | `N_rx × 12 bytes ÷ Δt` | `N_rx` = packets received; 12 = payload bytes excluding the 2-byte pseudo-sequence; unit bytes/s. Counts received bytes whether or not they contain errors, so it is not verified error-free goodput. The reports note that the course script labels the same quantity `bit/s`. |
| Experiment duration | `Δt` in seconds | Optimisation 1 only |
| Packet reception rate PRR | Optimisation 2 only; described as comparing the expected time for N packets at 100 % reception with the actual time taken | printed as `PRR = actual time ÷ expected time`, which is the inverse of what the tabulated percentages behave like; see [limitations-and-errata.md](limitations-and-errata.md) |

## 3. Optimisation 1: baud rate (report dated May 2026, 7 pages)

**Hypothesis (page 1).** Lowering the baud rate from the 100 kBaud baseline lengthens
the symbol time and should reduce the bit error rate, up to an optimum beyond which
further reduction stops helping. Configurations that reduce BER at the edge positions
need not help at the midpoint.

**Method (page 3).** Baud rates 100 (baseline), 80, 70, 60 and 50 kBaud, changed in the
tag firmware with the physical setup unchanged. The baseline was measured three times
and averaged; every other configuration once.

**Results (pages 4–6).** Table 1 lists BER, D/R and duration per baud rate and position;
Table 2 gives per-configuration averages; Figures 3–5 plot them. The transcriptions are
in [`data/reported/`](../data/reported/) and the tables are reproduced in
[results.md](results.md).

**The report's conclusions (page 7).** 80 kBaud gave the best performance at the edge
positions but nothing at the midpoint; 70 kBaud was the only configuration that received
packets at the midpoint, with a BER of about 30 % and a run of over 200 s; 60 and
50 kBaud brought no further improvement; the optimal rate depends on whether reliability
at reachable positions or coverage of the midpoint is the priority. The report also
states that 70 kBaud has the best overall averages when the midpoint failures are
included, noting itself that this is partly because the other configurations contribute
"BER = 100 %" at the midpoint. One sentence in that paragraph, that 70 kBaud has the
shortest average duration, is contradicted by the report's own Table 2; see the errata.

## 4. Optimisation 2: 250 kBaud with longer packets (report dated May 2026, 6 pages)

**Hypothesis (page 1).** The laboratory environment has strong, variable interference.
A much higher baud rate with longer packets could push more data through brief windows
of low interference, and might match or beat the baseline in such an environment.

**Method (page 3).** Baud rate set to 250 kBaud and "the packet length was increased by
50 percent (from 11 bytes to 16 bytes)". The same five positions and the same baseline
(three averaged trials) were used. The Setup section repeats the 5-minute midpoint cap;
the Results section says failures were recorded after **15 minutes** "at that location".
The report does not say which payload length entered the D/R formula for the 250 kBaud
rows, and "11 bytes" does not correspond to any packet-size constant in the platform
firmware (default payload 14 bytes = 2 + 12, length field 15, frame 24 bytes).

**Results (pages 4–6).** Table 1 lists BER, D/R and PRR for the baseline and the
250 kBaud configuration (no duration column). Figures 4–6 plot BER, D/R and PRR for the
positions with reception.

**The report's conclusions (page 6).** The configuration did not improve on the baseline:
BER became "significantly worse"; the P1 data rate was "not far from" the baseline
(27.87 vs 29.16 bytes/s, so close to but below it) while every other position was much
worse; PRR at positions other than P1 was in the low single digits of percent; reception
came in short bursts rather than a steady stream. The group reports this as a negative
result that might behave differently in an environment with different interference.

## 5. What the reports do not record

* the PIO clock dividers, deviation and receiver filter bandwidth per baud rate, and the
  SmartRF receiver settings used;
* the transmit spacing between packets in the laboratory firmware;
* the carrier output power, and whether one or two tag antennas were driven;
* the raw receiver logs, the exact packet counts, and the run durations for the
  250 kBaud configuration;
* the analysis code that produced the report figures (the report bar charts are not the
  course notebook's output);
* dates and environmental notes for each run.

These gaps are why the repository reproduces calculations from the published tables
rather than the experiments themselves ([provenance.md](provenance.md)).
