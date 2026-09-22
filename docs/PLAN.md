# PLAN — milestones in dependency order

Transcribed from §9.4 of `ARCHITECTURE.pdf`. Each milestone carries the acceptance test the
architecture record specifies. A box is ticked only when its acceptance test passes in `pytest`,
not when the code is written.

---

- [x] **M0 — Scaffold**
  Repo, environment, `CLAUDE.md`, the three `docs/` files, empty modules with docstrings, CI
  running `pytest`.
  *Accept:* `pytest` passes on an empty suite; `PLAN.md` lists M1–M9 with checkboxes.

- [ ] **M1 — config + space**
  Typed `CampaignConfig` (variables as a list; objectives as a list with sign; constraint mode and
  thresholds; kernel; `n_0`, budget, stopping; reference point; normalization ranges; `D_spool`,
  `l_f`, `v_f,0`, `d*`; power column mapping). JSON round-trip. `space.py`: raw ↔ unit cube; `R`
  from set-points; 3D rotated coordinates behind a flag with linear constraints.
  *Accept:* round-trip test; `R` test against hand calculation; 3D parallelogram constraint test.

  **Partially complete — 1 of 3 acceptance tests met.**
  - [x] JSON round-trip — `tests/test_config.py`, 29 tests.
  - [x] *(beyond the stated criterion)* raw ↔ unit-cube map — `tests/test_space.py`, 13 tests.
  - [ ] `R` against hand calculation — **blocked on open item G1**.
  - [ ] 3D parallelogram constraint — **blocked on G1, transitively**.

  > **A3 is answered and no longer blocks this** (15 mm bare core, ~33 mm full, 20 mm traverse,
  > spool emptied between runs). What blocks it now is **G1**, and the block has changed shape:
  > the quantity is no longer a missing constant but a missing *decision*. DECISIONS D14 settles
  > the physics — `D_end² − D_start² = 4·d_in²·v_f·t/(π·w) = 97.02 mm²` per 180 s run, independent
  > of `ω_s`, so `R` is a function of time within a run, `R(t) = π·D(t)·ω_s / v_f` — but the user
  > has asked G1 to stay open while we settle how the spool state enters the design point, and
  > which sleeve-free lever puts `d* = 0.40 mm` inside the box (it is not reachable on a bare core
  > at `ω_f = 0.30`: run-mean `d ∈ [0.4429, 0.6264]` mm over `ω_s ∈ [25, 50]`).
  >
  > `space.draw_ratio` and `space.linear_constraints` therefore still raise `NotImplementedError`,
  > naming G1, rather than being written against a signature that is about to change: a constant
  > `R` and a `R(t)` path do not have the same return type. The acceptance test
  > `test_draw_ratio_against_hand_calculation` is `xfail(strict=True)`, so it will fail loudly
  > the moment the decision lands and the implementation appears.

- [ ] **M2 — extraction + power**
  Algorithm 1; distinct-reading logic; equations (1)–(3); onset suggestion (Appendix A); power-log
  alignment by offset; PM source only (PX removed, DECISIONS D9).
  *Accept (as written in §9.4, against `fred_experiment_test.csv`):* declared BREAKAGE, suggested
  onset 147.5 s, window [0, 142.5] s, `d̄ = 0.427` mm, `N = 193`, `ρ̂₁ ≈ 0.90`, `N_eff ≈ 10`, trend
  warning true; a synthetic power log with known offset aligns to within 0.1 s.
  > **The fixture these numbers describe is not in hand.** The supplied
  > `fred_experiment_withgraphing.csv` is a format and schema reference only (see DECISIONS D2),
  > and contains no declared failure. The alignment sub-test can be met with synthetic fixtures
  > now; the onset and statistics assertions need a real run with a declared breakage. The PX
  > acceptance line of §9.4 is dropped (DECISIONS D9, confirmed). The power-log format is
  > `docs/POWER_LOG_REQUIREMENTS.docx` with `data/examples/power_log_example.csv` as the fixture
  > shape; the two temperature masks of DECISIONS D13 and the plateau-sd diagnostic are part of
  > this milestone's extraction.

- [ ] **M2b — per-run spool fields at intake** *(new, ahead of M3; open item H1 accepted)*
  The operator records `d_start_mm` and `d_end_mm` (vernier on the spool), the wound width, and
  the micrometer reading on the fibre, alongside the CSV upload. Stored per run and exported.
  *Accept:* a run whose measured `D_end` departs from the D14 prediction is flagged at intake,
  with the deviation and the recomputed `R̄` surfaced, not silently accepted.
  > H1 was accepted on 22 Sep 2026 and will be run **on a full spool** (DECISIONS D15), so these
  > fields have to exist before the calibration runs happen or their data cannot be entered. This
  > is the only piece of the H1 work that is software; the rest is bench time.

- [ ] **M3 — simulate**
  `FakeFrED`: `d = d_in/√R · g(T)` with a mild temperature effect, `power = a + b·T + c·ω_s²`,
  breakage above `R_hi(T)` and overflow below `R_lo(T)`, Gaussian run-to-run noise; writes device
  CSVs in the real schema (and optional power logs).
  *Accept:* generated files pass M2 extraction; failure regions match their definitions.
  > The emulator integrates the D14 spool path, so `d` drifts within a run exactly as the device's
  > does (−8.6 % on a bare core, −2.1 % from a full one). Writing it with a constant `R` would
  > produce fixtures that the trend check never fires on, and hide the problem M2 has to handle.

- [ ] **M4 — models**
  Algorithm 2; kernel choice; `FitReport` with hyperparameters, LML, the LML grid over (ℓ₁, ℓ₂),
  LOO residuals.
  *Accept:* on 30 emulator points the fitted length-scales are within a factor 3 of the
  emulator's, and the LML grid maximum coincides with the fitted point.

- [ ] **M5 — constraints + acquisition + pareto**
  Constraint callables from config (modes A/B); Pr(F) grid; objective transform; qLogNEHVI
  construction and `optimize_acqf`; R-band suggestion logic; observed and posterior-mean fronts;
  hypervolume; convergence signals (15)–(17).
  *Accept:* on the emulator with 6+20 runs, hypervolume is monotone non-decreasing and the final
  observed front beats Sobol-only at the same budget over 5 seeds; no proposed candidate has
  Pr(F) < 0.05 once the constraint GP has ≥ 8 points.

- [ ] **M6 — storage + campaign + export**
  SQLite schema of §6; `CampaignController` implementing Algorithm 3; save/resume; JSON +
  Markdown + CSV export.
  *Accept:* close and reopen mid-campaign yields an identical proposal and hypervolume; export
  validates against its JSON schema.

- [ ] **M6b — Target sessions**
  Session table; predicted iso-diameter curve and front for a new `d*` (§5.5); start-session
  action; per-session convergence; map grids and iso-diameter entries in the export.
  *Accept:* on the emulator, session 2 at a different `d*` converges in fewer runs than session 1
  under the same rule, and the front predicted before session 2 lies within its stated ±2σ band of
  the front measured after it.

- [ ] **M7 — CLI end-to-end**
  `run_campaign_cli.py` drives a full emulator campaign (intake, declare, fit, propose, converge,
  second target session, export) with no UI.
  *Accept:* runs unattended in < 5 min on CPU; produces the export files.

- [ ] **M8 — UI**
  PySide6 windows of §7.3, English only, calling only `CampaignController`; Matplotlib QtAgg
  canvases; the `q > 1` confirmation dialog; the kernel-lock behaviour.
  *Accept:* manual script in `docs/UI_CHECKLIST.md` completed; no computation in UI code.

- [ ] **M9 — Simulation tab + polish**
  qLogNEHVI vs. qNParEGO vs. Sobol on the emulator over seeds inside the app; packaging
  instructions; final pass over `docs/`.

- [ ] **M10 — Hardware bring-up** *(re-open when the power PCB arrives, §9.5)*
  Re-run the M2 fixture on a real power log, adjust the column mapping, validate the alignment.
  > The first campaign is PM/B (DECISIONS D9, open items G2/G3 confirmed), so M10 validates PM
  > on real hardware; the B→A switch is a separate, later decision.

---

## Hardware-unvalidated surfaces (§9.5)

Built now against the emulator only; flagged in `DECISIONS.md` until the power unit exists.

- Mode PM power ingestion (`power.py`): log parsing, column mapping, offset alignment, per-channel
  V·I. Real header names, sample rate and marker format are **expected to differ** from the config
  defaults — keep them all in config, never hard-coded.
- Mode A constraint: spooler-current margin GP, thresholds `τ_lo`/`τ_hi`, failed-run margins. The
  thresholds and the monotonicity assumption are unverified until experiment M3b.
- The alignment fallbacks (file timestamps, manual slide) must be fully working, not stubs — the
  PCB request list may be only partly granted.
- (Removed with mode PX, DECISIONS D9: there are no proxy constants any more.)

The first campaign runs **PM / mode B** (open items G2 and G3, confirmed 21 Sep 2026): the power PCB is a prerequisite, and the paper reports mode B with mode A parked.

## Bench work the plan now depends on

- **H1 — pre-campaign calibration runs. Accepted 22 Sep 2026, not yet run.** Empty-or-full spool
  (the user says full), `ω_f = 0.30`, `ω_s = 25 / 37.5 / 50`, micrometer on the fibre, vernier on
  the spool before and after. Measures the effective `ℓ_f` (D8/A4 leave it as an upper bound), the
  vision-minus-micrometer offset, the fill per run against D14, and the direction of the
  temperature effect. **It gates G1**, because no sleeve-free lever can be sized until `ℓ_f` is
  measured: a 15 % error in `ℓ_f` moves `d` by 7.8 %.
- **D2 — heater retune.** Still outstanding; the sample file sat ~5 °C below set-point.

Full list of blocking measurements: `../../FrED_MOBO_Open_Items.docx`.
