"""Section D — dominance, fronts, hypervolume and convergence.

Non-dominance, the hypervolume indicator with a fixed reference point, the
posterior-mean front on a grid, and the three convergence signals.

Two standing decisions live here. The reference point is fixed before the campaign and
never recomputed from data — a floating reference destroys hypervolume monotonicity.
And the final Pareto set is recommended from the *posterior mean*, never from raw
observed ``y`` (§1.3).

Objectives are normalized by a fixed pre-campaign affine map before hypervolume,
because um and W differ in scale and a large constant power baseline would otherwise
make the acquisition insensitive to real differences (§5.1, §9.2 item 1).

Implements: §5.1, §5.4, equations (12), (15)-(17)
Public interface (§7.1): ``observed_front``, ``posterior_front``, ``hv``, ``convergence``
"""
