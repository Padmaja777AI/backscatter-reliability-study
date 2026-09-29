# Analytical optimisation: packet-level FEC with interleaving (proposal)

**Author:** Padmaja Pabbathi, individual submission for the WCNES course (1DT195),
Uppsala University, June 2026. Full text:
[`reports/Pabbathi_Analytical_Optimisation_FEC_Interleaving.pdf`](reports/Pabbathi_Analytical_Optimisation_FEC_Interleaving.pdf).
The submission was accepted and awarded grade 5.

> **Status: analytical proposal only.** The report states that no additional experiments
> or simulations were performed. Nothing in this repository implements, simulates or
> measures the proposal, and no reliability improvement from it has been demonstrated.
> The expected benefits below are hypotheses that depend on the code chosen and on the
> actual error patterns of the link.

## 1. The limitation it addresses

In the experiments the only thing gating a packet was the sync word, which decides
whether the receiver accepts a packet but does not protect the payload. Accepted packets
still carried bit errors (about 10–18 % at baseline, several percent at 80 kBaud), and
there was no redundancy, parity or retransmission to recover them. Optimisation 2 also
showed clustered, bursty reception tied to interference. Neither baud-rate nor
packet-length tuning touched this coding layer.

## 2. Hypothesis

Adding lightweight forward error correction (FEC) and bit interleaving on top of the
better baud-rate configurations would be expected to improve *delivered* payload
reliability at positions where packets are received but corrupted. Interleaving would
spread burst errors across codewords so that each codeword sees an error count the FEC
can correct. The gain would be largest at the moderate-BER edge positions and would cost
useful throughput, latency and tag processing and memory.

## 3. Reasoning in the report

* **Dual-link constraint.** Received power depends on the product of both link budgets,
  which explains why positions near the carrier performed best and the midpoint worst
  (citing the LoRea backscatter architecture).
* **Symbol duration.** A lower baud rate lengthens the receiver's decision window per
  symbol, lowering the raw bit-error probability; coding does not change this window but
  operates on the bit errors it leaves.
* **Bit errors to packet errors.** For independent errors with probability *p* over
  *N* bits, `P(packet error) = 1 − (1 − p)^N`; longer raw packets (as in Optimisation 2)
  make this worse, which argues for redundancy rather than longer uncoded packets.
* **FEC** trades parity bits for correction of a bounded number of errors per codeword;
  simple block codes are the realistic choice on a constrained tag.
* **Interleaving** turns a bursty channel into something closer to the independent-error
  channel that FEC analysis assumes, which is why the two are proposed together.
* **What coding cannot do.** It acts only on packets that are detected and accepted.

## 4. Expected behaviour mapped onto the measured configurations

| Configuration | Measured situation (from the Group 6 tables) | Expected effect of FEC + interleaving (hypothesis) |
|---|---|---|
| 80 kBaud | lowest mean BER over the reached positions (4.30–10.00 %); no midpoint reception | best substrate for lightweight coding; delivered payload error rate expected to fall further, provided the code is strong enough for the higher-BER edge positions |
| 70 kBaud | only configuration reaching the midpoint, at about 30 % BER and 11.73 bytes/s | could improve the *quality* of the packets that do arrive, including the marginal midpoint reception, but cannot increase how many arrive; the midpoint stays weak |
| 250 kBaud + longer packets | BER 33–38 % at reached positions, two positions lost, PRR 1–2 % at P2/P4 | not expected to be rescued by coding: raw error rate and burstiness too severe at that operating point |
| Any position without reception | failure marker in the tables | no effect; coding cannot recover packets that were never detected |

## 5. Tradeoffs stated in the report

| Dimension | Cost |
|---|---|
| Useful throughput | parity bits displace data bits; significant for a link already at tens of bytes per second |
| Latency | the interleaver must buffer a block before transmission and before de-interleaving, and the coded packet takes longer to send |
| Processing and memory | encoding and interleaving add logic and buffers on the constrained tag |
| Packet length | stronger codes and deeper interleavers want larger blocks, while the Optimisation 2 result and the packet-error formula warn against long raw packets in this channel; interleaver depth must be balanced against exposure |

## 6. How this repository treats the proposal

* It is presented as an accepted analytical submission, separate from the hardware
  experiments.
* No figure or table in this repository shows a measured or simulated effect of coding.
* A natural next step, outside the scope of the submitted work, would be a simulation
  driven by the measured BER values, or an implementation in the tag firmware and the
  analysis notebook; neither has been done.

## References cited in the report

1. A. Varshney, O. Harms, C. Pérez-Penichet, C. Rohner, F. Hermans, T. Voigt, "LoRea: A
   Backscatter Architecture that Achieves a Long Communication Range", ACM SenSys 2017.
2. B. Sklar, *Digital Communications: Fundamentals and Applications*, 2nd ed., Prentice
   Hall, 2001.
3. Y. Q. Shi, X. M. Zhang, Z.-C. Ni, N. Ansari, "Interleaving for combating bursts of
   errors", IEEE Circuits and Systems Magazine, vol. 4, no. 1, 2004.
