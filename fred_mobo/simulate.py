"""Synthetic FrED emulator — offline only.

``FakeFrED`` writes device CSVs in the real schema so the whole pipeline can be tested
before hardware exists, and provides the qNParEGO / Sobol baselines.

Model: ``d = d_in/sqrt(R) * g(T)`` with a mild temperature effect,
``power = a + b*T + c*omega_s^2``, breakage above ``R_hi(T)``, overflow below
``R_lo(T)``, Gaussian run-to-run noise.

NEVER mixed with hardware data (§7.3 item 9).

Implements: §9.4 M3, §7.3 item 9 (simulation tab)
Public interface (§7.1): ``FakeFrED``
"""
