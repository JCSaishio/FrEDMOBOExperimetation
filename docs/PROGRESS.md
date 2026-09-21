# PROGRESS

Session log. Per §9.6 this is the first thing to read at the start of every session, and it must
always say exactly where to resume.

---

## Where to resume

**Next step: M3's I/O layer — the device-CSV writer *and* the power-log writer — in `simulate.py`.**
Neither depends on an open item. The power-log format is fixed by
`docs/POWER_LOG_REQUIREMENTS.docx` (F1–F10) and `PowerConfig`'s defaults; the device-CSV format is
`data/examples/fred_experiment_withgraphing.csv` (`;`, decimal comma, ~43 Hz log against ~3 Hz
sample-and-hold vision, 5.3 µm lattice). Together they are every fixture M2's extraction and
alignment tests need. The drawdown relation itself stays behind G1.

**If G1 is answered first, do M1 instead.** The user's Rev. 3 reply prefers `ω_s`; the Rev. 4
recommendation is option A (keep `ω_s`, "empty the spool before every run, same run length",
`R` from the set-point through `D_mid = D_core + ΔD/2` with `ΔD = 48.5/D` mm per 180 s run — or,
better, from the logged turns at the window midpoint). Hand value for the acceptance test on the
bare core: `R = π·15·30/(34.558·0.30) = 136.4`; at `D_mid = 16.62` it is 151.0. Under A+ (sleeve)
or B the signature is the same kinematic core with a different `d_eff_mm` source. Read
`FrED_MOBO_Open_Items.docx` item G1 for the user's choice. **If H1 is accepted**, the intake's
per-run fields (`d_start_mm`, `d_end_mm`, wound width, micrometer readings) come before M3, so the
calibration runs go straight into the database.

**Open-items state (Rev. 4, 21 Sep 2026).** 33 items; three yellow REPLY rows await the user:
**A2** (upper bound of the temperature box), **G1** (spool protocol and variable), **H1**
(calibration runs). Read them back with `REPLY ([A-H]\d+):\s*(.*)` on the first cell of every
table row; sentinel `[ type your reply here ]`. What the Rev. 3 replies changed in code:

| Item | Reply | Applied to |
|---|---|---|
| A2 | EVA; draws from 90 °C; 150 °C safety limit | `default_2d_campaign` box `[90, 120]` (upper provisional); D11 |
| A3 | facts confirmed; spool emptied between runs; sample sensor uncalibrated | D10 amended; the 23 mm inference withdrawn |
| A4 | no gearbox; 11 mm is the head's outer diameter | `l_f` kept at 34.558 as an **upper bound**; H1 measures it |
| E1 | 0.25 mm has been made "depending on temp"; keep ≈ 0.40 | `d_star_mm = 0.40`; sessions 2–3 provisionally 0.30 / 0.50 after H1 |
| E3 | 0.15 mm confirmed | already in config |
| E4 | warn 3 °C; band 1 °C (reaffirmed) | `delta_t_warn_c = 3.0`, `delta_t_c = 1.0`; D12 |
| E5 | ±10 °C; low-pass suggested | `temp_setpoint_tolerance_c = 10`, `temp_plausible_c = (0, 160)`; no filter; D13 |
| G2 | Yes | PX removed from `config.py`/`power.py`/tests; PLAN M2/M10; D9 confirmed |
| G3 | Yes | mode A parked; PLAN M10 |
| G1 | prefers `ω_s`; asks for more options | re-opened with options A/A+/B/C/D; nothing in code |

`pytest`: 83 passed, 1 xfailed.

---

## Done

### M0 — Scaffold · 21 Sep 2026

Complete. Acceptance test met: `pytest` exits 0, and `docs/PLAN.md` lists M1–M9 with checkboxes.

- Repo tree per §9.3: `fred_mobo/` with the twelve backend modules, `ui/` and `ui/tabs/`,
  `scripts/`, `tests/`, `docs/`, `data/examples/`.
- All backend modules created with a module docstring naming the architecture section they
  implement. No function bodies yet — that is deliberate, M0 is layout only.
- `environment.yml` pinned against the `fred-mobo` miniforge env that already existed on this
  machine: Python 3.12.13, **botorch 0.18.1** (the version §8 was verified against), gpytorch
  1.15.2, torch 2.13.0+cpu, linear_operator 0.6.1, numpy 2.5.1, pandas 3.0.5, scipy 1.18.0,
  matplotlib 3.11.1, pytest 9.1.1. PySide6 is commented out until M8 (DECISIONS D4).
- `CLAUDE.md` written to the §9.3 cap of 40 lines.
- CI at `.github/workflows/ci.yml` runs `pytest` on push and PR.
- `docs/ARCHITECTURE.pdf` and `data/examples/fred_experiment_withgraphing.csv` copied in so the
  repo is self-contained.

**Verified by:** `tests/test_scaffold.py` — asserts every module named in §9.3 exists and imports,
that `CLAUDE.md` is within its 40-line cap, and that `PLAN.md` lists M1–M9. The remaining test
files are docstring-only placeholders, one per milestone, so the suite is "empty" in the sense
§9.4 means while still collecting and exiting 0.

**Not done in M0, by design:** no logic in any module; no UI (§9.2 item 11 forbids it until the
CLI runs end-to-end).

Committed as `30737db` and pushed to `origin/main`. 50 files.

### M1 — config + space (partial) · 21 Sep 2026

`pytest`: **80 passed, 1 xfailed**. Only the unblocked parts were built, on instruction.

**Complete — `config.py`.** Typed `CampaignConfig` with everything §9.4 M1 lists. Variables and
objectives are *lists*, so `d` and `M` are not baked in (§7.4): `test_n_initial_follows_dimension_
without_a_code_change` adds a third variable and gets `n_0 = 8` with no code edit. `n_0 = 2(d+1)`
is a derived property, not a stored field — §9.2 item 7 makes it the one numeric the operator may
not edit, and a property cannot be edited into an inconsistent state. Frozen dataclasses
throughout, so a campaign edit is a logged event producing a new config rather than an in-place
mutation. `save()` validates before writing, so a broken config can never reach disk and be
reloaded on resume.

Validation rejects: inverted bounds, a single objective, duplicate names, a reference point better
than ideal, ideal worse than nadir, ARD-free kernels (§9.8), an empty or absent constraint band, a
target outside the plausibility range, and out-of-range stopping parameters.

**Complete — the coordinate map in `space.py`.** `bounds`, `unit_bounds`, `to_unit`, `from_unit`,
built on the verified `botorch.utils.transforms.normalize/unnormalize` signatures. Double
precision throughout (§9.2 item 1). Batch shapes preserved, so `b x q x d` tensors survive. A
trailing-dimension mismatch raises rather than broadcasting silently — that is exactly the
"mismatched spaces" bug §8 warns about.

**Deliberately not built — blocked on A3.** `space.draw_ratio` and `space.linear_constraints`
raise `NotImplementedError` naming the open item, with the reasoning in their docstrings and a
`TODO(resume)`. `tests/test_space.py` asserts they refuse to run, so the block is visible in the
suite rather than silently absent, and carries the parked acceptance test as
`xfail(strict=True)` — it will fail loudly once the implementation lands.

**Verified by:** `tests/test_config.py` (29 tests), `tests/test_space.py` (13 passed + 1 xfail).

---

## Open threads

- Git identity is set **repo-locally** (DECISIONS D5) to the GitHub noreply address, so the
  institutional email is not published in the history of a public repo. Say so if a different
  authorship is wanted — the history is one commit deep and can still be rewritten cheaply.
- 33 open items are tracked in `../../FrED_MOBO_Open_Items.docx` (Rev. 4). **G1** (spool
  protocol and design variable) gates M1; **H1** (calibration runs) decides `ω_f`, the session
  targets and whether `l_f`'s bound needs replacing; **A2** is one number (the box's upper bound).
- The repo has no licence yet (`README.md` says so). It is public, so this is worth deciding
  before there is anything in it worth copying.
