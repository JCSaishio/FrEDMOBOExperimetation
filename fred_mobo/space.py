"""Variable definitions and coordinate maps.

Maps raw engineering set-points to and from the normalized unit cube the GPs and the
acquisition live in, and computes the draw ratio ``R = v_s / v_f`` from set-points.

In 2D, ``v_f`` is fixed, so ``R`` is a known exact function of the spooler set-point;
the unknown is only where the failure boundaries sit in ``R`` and how they move with
``T`` (§4.1). For 3D this switches to the rotated coordinates ``(log R, log v_f, T)``,
whose rectangular raw bounds become a parallelogram expressed as linear inequality
constraints passed to ``optimize_acqf`` (§7.4).

Implements: §1.1, §2.3 step 10 (draw ratio), §7.4 (rotated coordinates)
Public interface (§7.1): ``to_unit``, ``from_unit``, ``bounds``, ``linear_constraints``
"""
