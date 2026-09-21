# PROGRESS

Session log. Per §9.6 this is the first thing to read at the start of every session, and it must
always say exactly where to resume.

---

## Where to resume

**Next step: M1 — `config.py` and `space.py`.**

Start with `CampaignConfig` and its JSON round-trip (`tests/test_config.py`), because everything
else takes a config. Then `space.py`: the raw ↔ unit-cube map, `R` from set-points, and the 3D
rotated coordinates behind a flag.

Do **not** assert a numeric value for `R` against a hand calculation yet — open items A1 (preform
diameter `d_in`, provisionally 7 mm) and A3 (effective spool diameter under load) are unresolved,
so the expected value is not known. Write the `R` test parametrized over `(D_spool, l_f, omega_s,
omega_f, d_in)` and mark the numeric-acceptance case `xfail(strict=False)` with a comment pointing
at A1/A3. The formula itself can and should be tested against its own algebra now.

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
CLI runs end-to-end); nothing pushed to the remote (`gh` was not authenticated at the time —
see DECISIONS D5).

---

## Open threads

- `gh auth login` had not been run when M0 was committed, so the remote
  `github.com/JCSaishio/FrEDMOBOExperimetation` is still empty. Push M0 once auth is in place.
- Git identity was set **repo-locally** (DECISIONS D5), not globally. Confirm the name and email
  on the first commit are the ones the user wants on a public repo.
- 28 open items are tracked in `../../FrED_MOBO_Open_Items.docx`; 7 are blocking. A1, A3 and E5
  are the ones that touch code in the next two milestones.
