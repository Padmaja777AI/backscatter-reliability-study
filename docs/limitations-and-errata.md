# Limitations and errata

This page collects (a) the limits of the evidence behind the results and (b) internal
inconsistencies found while transcribing the reports. Nothing has been corrected in the
transcriptions: the CSVs under [`data/reported/`](../data/reported/) hold the values as
printed, and the notes below say how they should be read.

## A. Limits of the evidence

1. **Single trials.** Every optimised configuration (80, 70, 60, 50 and 250 kBaud) was
   measured once per position; only the 100 kBaud baseline was repeated (three trials,
   averaged). Differences such as 7.35 % versus 7.86 % mean BER between 80 and 60 kBaud
   are within plausible run-to-run variation, so the results indicate trends but do not
   establish statistical significance or a universal optimum.
2. **No raw logs.** The receiver logs, packet counts and analysis scripts behind the
   tables are not available (see [provenance.md](provenance.md)). Every number in this
   repository derives from the published, rounded tables.
3. **Undocumented radio settings.** The reports do not give the PIO clock dividers,
   deviation, receiver filter bandwidth, SmartRF settings, carrier power, antenna
   configuration or transmit spacing used for each configuration.
4. **BER over received packets only.** Lost packets do not enter the BER, so a
   configuration can show a low BER and still deliver little data. The reports say this
   and add the data-rate and duration metrics for that reason.
5. **"Effective data rate" counts received bytes, not correct bytes.** D/R is received
   packets × 12 payload bytes ÷ duration; a packet with bit errors counts in full. It
   must not be read as verified error-free goodput.
6. **Failure markers in averages.** The reports enter "BER = 100 %" and "D/R = 0" for
   positions without reception. The 0 bytes/s is a legitimate throughput outcome; the
   100 % BER is an artificial marker, and any average that includes it (the reports'
   Table 2 BER column) mixes measurements with a sentinel and should not be read as a
   bit-error ratio. This repository reports such averages only under the label
   "sentinel-inclusive" and uses the four positions with reception in every compared
   configuration (P1, P2, P4, P5) for BER comparisons.
7. **Environment.** The laboratory had strong, variable interference (Optimisation 2,
   page 1); it was not characterised, and run dates are not recorded.

## B. Inconsistencies in the reports (recorded, not corrected)

### Optimisation 1 (baud rate)

1. **70 kBaud mean duration.** Re-applying Table 2's stated method to the published
   Table 1 values gives 105.29 s for 70 kBaud against 105.30 s in Table 2 (all other
   Table 2 entries reproduce exactly). The cause of the 0.01 s difference is not
   established from the published material.
2. **"Shortest average experiment duration."** The Discussion (page 7) says 70 kBaud
   achieves "the shortest average experiment duration of 105.30 s". Table 2 ranks the
   average duration 80k 71.41 s < 60k 74.85 s < 100k 97.04 s < 70k 105.30 s <
   50k 126.89 s, so 70 kBaud is fourth of five. Its average is also the only one taken
   over five positions (it includes the 204.53 s midpoint run), so the column is not
   like-for-like. Over the four common positions 70 kBaud averages 80.48 s, still longer
   than 80 and 60 kBaud.
3. **"Best overall" and the failure marker.** The report's statement that 70 kBaud has
   the best overall BER (14.06 %) and D/R (27.06 bytes/s) rests on Table 2's
   sentinel-inclusive averages, as the report itself notes. Two things are true at once:
   the BER lead is largely an artefact of the other configurations' 100 % markers, while
   the D/R lead (0.08 bytes/s over 80 kBaud) reflects a real coverage advantage, because
   70 kBaud did deliver 11.73 bytes/s at the midpoint where the others delivered nothing.
   The midpoint reception itself is a genuine finding, not an artefact.
4. **"Lowest BER and highest data rate among the edge positions" for 80 kBaud.** True as
   an unweighted average over P1, P2, P4 and P5 (7.35 %, 33.73 bytes/s), not at every
   position: 60 kBaud has the lower BER at P1 (3.57 vs 4.30 %) and P2 (8.64 vs 10.00 %),
   70 kBaud the higher data rate at P1 (39.72 vs 37.03 bytes/s), and 60 kBaud the higher
   data rate at P2 and P5. 80 kBaud is best on all three metrics at P4 and on BER at P5.
5. **Baseline packet count.** The Metrics section checks the D/R formula with
   205 packets for baseline P1, whereas the protocol says logging stopped at 200. For the
   baseline this multiplies two separately averaged quantities (mean D/R and mean
   duration of three trials), so the implied count is only an approximate consistency
   check; the same applies to every implied count in
   `analysis/output/opt1_implied_packet_count_check.csv`.

### Optimisation 2 (250 kBaud with longer packets)

6. **PRR formula.** Page 3 prints `PRR = actual time taken for N packets ÷ expected time
   taken for N packets`, a ratio that is ≥ 1 when packets are lost. The tabulated
   percentages (64.3 … 1) behave like the inverse, expected ÷ actual, and under that
   reading the baseline rows imply an inter-packet interval of about 0.26 s, which is
   plausible for the platform's configured 250 ms transmit delay plus overhead. The
   formula as printed and the values as printed are both preserved.
7. **Units.** The course notebook labels its data-rate output `bit/s` although it
   computes bytes per second; the reports say so and use bytes/s. Figure 5 of the
   Optimisation 2 report still carries the axis label "Data rate bit/s" while its Table 1
   says byte/s.
8. **Packet length.** "Increased by 50 percent (from 11 bytes to 16 bytes)" is a 45 %
   increase, and 11 bytes matches no packet-size quantity in the platform's starter code
   (default payload 14 bytes = 2 + 12 data, length field 15, frame 24). The D/R definition fixes
   the payload at 12 bytes; the report does not say which length entered the formula for
   the 250 kBaud rows. Under the expected-÷-actual reading of PRR, the 250 kBaud P1 pair
   (27.87 bytes/s, 46.5 %) is consistent with a 16-byte payload having been used and the
   P2 pair with 12 bytes, so the question is left open.
9. **P4 row.** D/R 11.2 bytes/s and PRR 1 % cannot both hold under the report's
   definitions (the diagnostic ratio in
   `analysis/output/opt2_baseline_vs_250k_comparison.csv` is 0.011 s where every other
   row gives 0.20–0.27 s). One of the two values is probably a transcription or
   computation slip in the report; both are kept as printed.
10. **Timeouts and failure rule.** The Setup section (copied from Optimisation 1) caps
    the midpoint run at 5 minutes; the Results section says failures were recorded after
    15 minutes "at that location"; and the failure marker is applied to P5, for which the
    Setup section defines no rule.
11. **Table caption and columns.** Table 1's caption promises BER, data rate and
    experiment duration, but the third column is PRR and no duration is reported, so the
    250 kBaud data rates cannot be cross-checked against packet counts.
12. **Cross-references and formatting.** The text says "Figure 6 shows the BER" (Figure 6
    is PRR; Figure 4 is BER), contains two unresolved "Figure ??" references, and prints
    the P2 data rate as ".93".
13. **"Not far from the baseline" at P1.** The P1 data rate of the 250 kBaud
    configuration (27.87 bytes/s) is close to but lower than the baseline
    (29.16 bytes/s), while its BER is about three times the baseline value there.
    The BER increase is not uniform across positions (factors of 3.13, 2.89 and 1.86 at
    P1, P2 and P4).

### Analytical report

14. "80k gave the best bit error rate at the reachable edge positions" (page 1) is
    correct as an average over those positions, with the per-position caveat in item 4.
    "70k … BER ≈ 30 % and a long experiment duration" at the midpoint matches Table 1
    (29.96 %, 204.53 s).

## C. How the README uses these findings

The README and [results.md](results.md) state the common-position averages and the
per-position winners separately, present the midpoint as a coverage result, never
average the 100 % marker as a BER, describe the 250 kBaud P1 data rate as close to but
below baseline, keep the PRR values as printed with a pointer to item 6, and present the
FEC proposal as unimplemented.
