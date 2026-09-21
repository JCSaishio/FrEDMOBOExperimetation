"""Section A.4 — the power objective, from the PCB's own log (mode PM only).

The power-measurement unit is a separate microcontroller with its own clock and its own
log; it is not synchronized with the device log. §2.4 built two sources; mode PX (the
proxy from PID duty and a calibration table) was removed on the user's instruction on
21 Sep 2026 (open items B5/G2, DECISIONS D9), so this module reads one format — the one
specified in ``docs/POWER_LOG_REQUIREMENTS.docx`` and shown in
``data/examples/power_log_example.csv`` — and ``power_source`` is recorded as PM on every
run for the record's schema.

``P(t) = sum_c V_c(t) I_c(t)`` per row, averaged over the aligned window. Empty cells are
missing samples (F7): counted and reported, never zero-filled or interpolated.

Alignment is by a stored offset and needs only ~1 s accuracy, because both objectives
are window means over tens of seconds. Offset comes, in order of preference, from a run
marker in both logs, the file creation timestamps, or the operator sliding the overlaid
traces.

HARDWARE-UNVALIDATED (§9.5): real header names, sample rate and marker format are
expected to differ from the config defaults. Keep them all in the config mapping, never
hard-coded, so a schema change is a config edit plus one fixture update.

Implements: §2.4 (mode PM, offset alignment)
Public interface (§7.1): ``read_power_log``, ``align``, ``mean_power``
"""
