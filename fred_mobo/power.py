"""Section A.4 — the power objective, two sources by priority.

The power-measurement unit is a separate microcontroller with its own clock and its own
log; it is not synchronized with the device log. Both source modes are built and the
one actually used is recorded per run in ``power_source``, so the two never pool
silently.

Mode PM (preferred, once the unit exists): ``P(t) = sum_c V_c(t) I_c(t)``, averaged over
the aligned window. Mode PX (proxy, until then): heater from the logged clamped PID
duty times ``P_h_max``, spooler from a current-vs-RPM calibration table, extruder a
constant. PX cannot see load-dependent heater power; it is a bridge, and the paper
reports which runs used it.

Alignment is by a stored offset and needs only ~1 s accuracy, because both objectives
are window means over tens of seconds. Offset comes, in order of preference, from a run
marker in both logs, the file creation timestamps, or the operator sliding the overlaid
traces.

HARDWARE-UNVALIDATED (§9.5): real header names, sample rate and marker format are
expected to differ from the config defaults. Keep them all in the config mapping, never
hard-coded, so a schema change is a config edit plus one fixture update.

Implements: §2.4 (modes PM and PX, offset alignment)
Public interface (§7.1): ``read_power_log``, ``align``, ``mean_power``
"""
