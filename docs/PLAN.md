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
  - [ ] `R` against hand calculation — **blocked on open item A3**.
  - [ ] 3D parallelogram constraint — **blocked on A3, transitively**.

  > Only **A3** blocks this milestone, not A1. `d_in` enters `d_out = d_in/√R`, which lives in
  > the emulator at M3; `R` itself needs the *effective* spool diameter, which is A3. The core
  > diameter (15 mm) and the value the observed drawdown implies (~34 mm) disagree by 2.3×, and
  > §4.1 calls `R` "the leading quantity for the constraint", so guessing would propagate into
  > the constraint model, the iso-diameter inversion and the 3D coordinates.
  >
  > `space.draw_ratio` and `space.linear_constraints` therefore raise `NotImplementedError`
  > naming A3, rather than being written against a guessed constant. The acceptance test
  > `test_draw_ratio_against_hand_calculation` is `xfail(strict=True)`, so it will fail loudly
  > the moment the value lands and the implementation appears.

- [ ] **M2 — extraction + power**
  Algorithm 1; distinct-reading logic; equations (1)–(3); onset suggestion (Appendix A); power-log
  alignment by offset; PM and PX sources.
  *Accept (as written in §9.4, against `fred_experiment_test.csv`):* declared BREAKAGE, suggested
  onset 147.5 s, window [0, 142.5] s, `d̄ = 0.427` mm, `N = 193`, `ρ̂₁ ≈ 0.90`, `N_eff ≈ 10`, trend
  warning true; PX heater power equals mean duty × `P_h,max` / 100; a synthetic power log with
  known offset aligns to within 0.1 s.
  > **The fixture these numbers describe is not in hand.** The supplied
  > `fred_experiment_withgraphing.csv` is a format and schema reference only (see DECISIONS D2),
  > and contains no declared failure. The alignment and PX sub-tests can be met with synthetic
  > fixtures now; the onset and statistics assertions need a real run with a declared breakage.

- [ ] **M3 — simulate**
  `FakeFrED`: `d = d_in/√R · g(T)` with a mild temperature effect, `power = a + b·T + c·ω_s²`,
  breakage above `R_hi(T)` and overflow below `R_lo(T)`, Gaussian run-to-run noise; writes device
  CSVs in the real schema (and optional power logs).
  *Accept:* generated files pass M2 extraction; failure regions match their definitions.

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
  Re-run the M2 fixture on a real power log, adjust the column mapping, validate the alignment,
  and switch the campaign config from PX/B to PM/A only if the operator confirms.

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
- The extruder constant `P_f,0` and the load dependence of heater power are unknown; PX values are
  operator-entered placeholders and are flagged as such in the export.

Until then the first campaign runs **PX / mode B**, and the paper reports that.

Full list of blocking measurements: `../../FrED_MOBO_Open_Items.docx`.
