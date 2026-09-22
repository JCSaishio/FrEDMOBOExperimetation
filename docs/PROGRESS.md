# PROGRESS

Session log. Per §9.6 this is the first thing to read at the start of every session, and it must
always say exactly where to resume.

---

## Where to resume

**Next step: M2b — the per-run spool fields at intake** (`d_start_mm`, `d_end_mm`, wound width,
micrometer reading), then M3's I/O layer in `simulate.py`. M2b moved ahead of M3 because open item
**H1 was accepted on 22 Sep 2026** and will be run on a full spool (DECISIONS D15): the fields have
to exist before the calibration runs happen, or their data cannot be entered. Neither depends on a
pending answer.

The power-log format is fixed by `docs/POWER_LOG_REQUIREMENTS.docx` (F1–F10) and `PowerConfig`'s
defaults; the device-CSV format is `data/examples/fred_experiment_withgraphing.csv` (`;`, decimal
comma, ~43 Hz log against ~3 Hz sample-and-hold vision, 5.3 µm lattice). Together they are every
fixture M2's extraction and alignment tests need.

**The drawdown relation itself stays behind G1**, which the user has explicitly asked to keep open.
DECISIONS **D14** now settles the physics under it, so when G1 lands the implementation is short:
`D_end² − D_start² = 4·d_in²·v_f·t/(π·w) = 97.02 mm²` per 180 s run at `ω_f = 0.30`, independent of
`ω_s`; `R(t) = π·D(t)·ω_s / v_f`; bare-core hand values `D: 15 → 17.9449 mm`, `R: 136.4 → 163.1` at
30 RPM. Note the signature question this raises — `draw_ratio` must return a *path*, or a
window-mean `R̄`, not a scalar `R` — which is why it is still `NotImplementedError`.

**Open-items state — all three yellow rows answered, read from the SAVED document
(22 Sep 2026, 11:09).** An earlier reading in this session came from Word's AutoRecovery snapshot
because the file was still open and unsaved; the saved G1 and H1 replies turned out to say more
than that snapshot did, so *the AutoRecovery text is superseded and must not be reused*.

| Item | Saved reply | Outcome |
|---|---|---|
| **A2** | box may be wider; "this 130 is fine" | **CLOSED.** Box `[90, 130]`, commit `310b917`, D11 settled |
| **G1** | adopts the layer model; asks to *keep the item open*; rules out the printed sleeve | **STILL OPEN**, by the user's instruction. Physics settled in **D14**; one narrowed question goes to Rev. 5 |
| **H1** | "I'll run those as soon as I can with the full spool and vision system updated" | **ACCEPTED.** D15; creates milestone **M2b** |

Two things in the saved G1 reply that changed the analysis and are worth not re-deriving:

- The user's premise — "the amount of fiber in the spool is determined by the spooling speed" —
  does not survive their own model. `ω_s` cancels out of the fill (D14). Their *goal*, standardising
  the final spool diameter, is therefore already delivered by the emptied-spool protocol they
  follow, at no cost.
- **The printed sleeve (option A+) is withdrawn.** "lets discuss how to expand A without the
  printed sleeve." The sleeve-free levers, measured: widen the `ω_s` box (0.40 mm needs 61.3 RPM
  on a bare core, so a box like `[25, 97.6]` — a device question: what is the spooler's maximum?);
  lower `ω_f` to 0.177 RPM (0.40 mm at the box centre, but 41 % less fibre per run); or place the
  steady-state window late in the run (drift across the last third is 2.8 lattice steps against
  9.7 across the whole run, at the cost of `N_eff`). None can be *sized* before H1 measures `ℓ_f`.

Read replies back with `REPLY ([A-H]\d+):\s*(.*)` on the first cell of every table row; sentinel
`[ type your reply here ]`. If the sentinels are still there but the user says they answered, the
file is open in Word — check for the `~$` lock file beside it. What the Rev. 3 replies changed in
code:

| Item | Reply | Applied to |
|---|---|---|
| A2 | EVA; draws from 90 °C; 150 °C safety limit; **upper bound widened to 130** (22 Sep, verified against the saved file) | `default_2d_campaign` box `[90, 130]`; D11 rewritten as settled; `test_space` corners and midpoint follow |
| A3 | facts confirmed; spool emptied between runs; sample sensor uncalibrated | D10 amended; the 23 mm inference withdrawn |
| A4 | no gearbox; 11 mm is the head's outer diameter | `l_f` kept at 34.558 as an **upper bound**; H1 measures it |
| E1 | 0.25 mm has been made "depending on temp"; keep ≈ 0.40 | `d_star_mm = 0.40`; sessions 2–3 provisionally 0.30 / 0.50 after H1 |
| E3 | 0.15 mm confirmed | already in config |
| E4 | warn 3 °C; band 1 °C (reaffirmed) | `delta_t_warn_c = 3.0`, `delta_t_c = 1.0`; D12 |
| E5 | ±10 °C; low-pass suggested | `temp_setpoint_tolerance_c = 10`, `temp_plausible_c = (0, 160)`; no filter; D13 |
| G2 | Yes | PX removed from `config.py`/`power.py`/tests; PLAN M2/M10; D9 confirmed |
| G3 | Yes | mode A parked; PLAN M10 |
| G1 | Rev. 5: adopts the layer model, keeps the item open, rules out the sleeve | physics recorded in D14; `draw_ratio` still `NotImplementedError`; nothing else in code |

`pytest`: 84 passed, 1 xfailed (`6c4b8e2` fixed a Linux glob-order failure in `test_scaffold.py` and added a shape test for `power_log_example.csv`; CI green).

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
- 33 open items are tracked in `../../FrED_MOBO_Open_Items.docx`. **G1** is the only one still
  open and it still gates M1; **H1** is accepted and unscheduled, and it gates G1 in turn, because
  no sleeve-free lever can be sized until `ℓ_f` is measured (a 15 % error in `ℓ_f` moves `d` by
  7.8 %). **A2 is closed.** Rev. 5 of the document is the next thing to build.
- **The user's open question, carried into Rev. 5:** "how this transfers to the points." D14 gives
  half the answer — under the emptied-spool protocol the `D`-path is identical for every run, so
  `ω_s` stays the coordinate and the vernier reading is a protocol check rather than a GP input.
  The other half is the errors-in-variables case they are gesturing at, which only becomes live if
  the protocol stops emptying the spool.
- The repo has no licence yet (`README.md` says so). It is public, so this is worth deciding
  before there is anything in it worth copying.
