"""Section A — diameter data extraction.

Algorithm 1. Turns one device CSV plus the operator's declaration into a
``RunRecord``: a representative steady-state diameter and its uncertainty.

Two properties of the device log drive the design. The vision system updates at ~3 Hz
while the logger writes at ~45 Hz, so only *distinct* readings count as observations
(treating every row as one overstates the sample size ~15x). And distinct readings are
strongly autocorrelated, so the standard error uses the AR(1) effective sample size of
equation (3) — without it the SE is understated by roughly 4x.

What this module deliberately does NOT do (§2.1): it does not detect breakage or
overflow, and it does not correct, mask or model temperature-loop disturbances.
Failures are *declared* by the operator. See DECISIONS D3 for the one narrow exception
agreed for physically-impossible temperature sensor drop-outs.

Implements: §2 Algorithm 1, equations (1)-(3), Appendix A (onset suggestion)
Public interface (§7.1): ``extract_run(csv, declaration, cfg) -> RunRecord``
"""
