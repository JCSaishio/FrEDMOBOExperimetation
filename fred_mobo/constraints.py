"""Section C — constraints.

Feasibility is a *band*, ``tau_lo <= c(x) <= tau_hi``, expressed to BoTorch as two
outcome constraints on one GP output in the convention 'g(y) <= 0 is feasible'.

Feasibility enters the acquisition as ``E[HVI * 1{g1<=0} * 1{g2<=0}]`` with the
indicators evaluated on each joint posterior sample — never as ``E[HVI] * Pr(F)``. The
design record shows the product form overstates by 57 % under strong negative
correlation, and always toward riskier settings (§4.2, §9.2 item 4).

Mode B (default, available today): R-band from declared failures plus a diameter band
on the already-modeled ``d``. Mode A (needs the spooler current channel): a margin GP on
mean armature current. Same code path in both — a config entry names the outcome column
carrying the constraint and its two thresholds.

HARDWARE-UNVALIDATED (§9.5): mode A's thresholds and its monotonicity assumption are
unverified until experiment M3b.

Implements: §4, equations (10)-(11)
Public interface (§7.1): ``make_constraints(cfg)``, ``prob_feasible(model, X)``
"""
