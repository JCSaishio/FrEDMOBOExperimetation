"""Algorithm 3 — campaign orchestration.

The outer loop, and the only module the UI is allowed to call.

Sequential by default (``q = 1``) because the device runs one experiment at a time.
Initialization is ``n_0 = 2(d+1) = 6`` Sobol points with the extreme spooler values
forced in at mid-temperature — with only two objectives nothing rewards high speed, so
the constraint boundary up there would otherwise be under-sampled (§5.3).

Declared failures do NOT count against the adaptive budget: they usually fail early and
cost little, so the loop counts OK runs only (§1.3 item x).

Implements: §5.3 Algorithm 3, §5.5 (target sessions)
Public interface (§7.1): ``CampaignController``
"""
