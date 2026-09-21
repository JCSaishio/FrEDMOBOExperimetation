# PROGRESS

Session log. Per §9.6 this is the first thing to read at the start of every session, and it must
always say exactly where to resume.

---

## Where to resume

**Next step: M3's I/O layer — the device-CSV writer *and* the power-log writer — in `simulate.py`.**
Neither depends on an open item. The power-log format is now fixed by
`docs/POWER_LOG_REQUIREMENTS.docx` (F1–F10) with `data/examples/power_log_example.csv` as the
exact shape; the device-CSV format is `data/examples/fred_experiment_withgraphing.csv` (`;`,
decimal comma, ~43 Hz log against ~3 Hz sample-and-hold vision, 5.3 µm lattice). Together they
are every fixture M2's extraction and alignment tests need. The drawdown relation itself stays
behind G1.

**If G1 is answered first, do that instead:** implement `space.draw_ratio` (hand value
`R = π·15·30/(34.558·0.30) = 136.4` on the bare core at 30 RPM), delete the `xfail` on
`tests/test_space.py::test_draw_ratio_against_hand_calculation`, implement
`space.linear_constraints`, and close M1. Under option B (R as the design variable) the box in
`space.py` is on R and the intake gains a per-run `d_eff_mm`; under option A it is on `ω_s` with
`d_spool_mm` fixed. Read `FrED_MOBO_Open_Items.docx` item G1 for the user's choice.

**Open-items state (Rev. 3, 21 Sep 2026).** All 29 Rev. 2 answers were read back and responded
to; the document one level up is now Rev. 3 with 32 items and ten yellow REPLY rows awaiting the
user: A2, A3, A4, E1, E3, E4, E5, G1, G2, G3. Read them back with the regex
`REPLY ([A-G]\d+):\s*(.*)` on the first cell of every table row; the sentinel is
`[ type your reply here ]`. What each answer changed in code, so nothing is applied twice:

| Item | Answer | Applied to |
|---|---|---|
| A1 | `d_in = 7 mm` confirmed | `DeviceConfig` docstring; no longer provisional |
| A3 | core 15 mm, full ≈ 33 mm, 20 mm traverse, "estimate for now" | DECISIONS D10; `space.py` block renamed to G1 |
| A4 | `ℓ_f = π·11 = 34.558 mm/rev` | `DeviceConfig.l_f_mm_per_rev`; DECISIONS D8 |
| B1, B5 | PCB "most likely"; drop PX, PM only | DECISIONS D9 — **code untouched until G2 confirmed** |
| B2–B4 | (moot under PM) | nothing; closed |
| B6–B9 | requirements file requested | `docs/POWER_LOG_REQUIREMENTS.docx`, `data/examples/power_log_example.csv` |
| C4 | mode B, band editable | already the default; mode A stays a config option (G3) |
| D1 | mask, surface the count | already DECISIONS D3; range still E5 |
| E2 | (explained) `f₁` ideal 0 / nadir 0.15 | already the `default_2d_campaign` values |
| F3 | all installs approved | memory only |

Not yet applied, waiting on a reply: the temperature box (A2), the `d*` list (E1: 0.40 first is
the user's provisional choice — `default_2d_campaign(d_star_mm=0.35)` still carries the old
placeholder), `delta_t_warn_c` and `delta_t_c` (E4), `temp_plausible_c` (E5: proposed [40, 130]).

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
- 32 open items are tracked in `../../FrED_MOBO_Open_Items.docx` (Rev. 3). The one that gates
  everything is **G1** — which variable the GP sees now that the spool diameter is known to vary
  by a factor 2.2 over a campaign. G2 (PX removed) and E5 (temperature mask range) are the other
  two that move code as soon as they are answered.
- The repo has no licence yet (`README.md` says so). It is public, so this is worth deciding
  before there is anything in it worth copying.
