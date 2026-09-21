# DECISIONS

Deviations from `ARCHITECTURE.pdf`, and choices made where the record is silent (§9.1: "Where the
document is silent, choose the simplest option, record it in `docs/DECISIONS.md`, and continue").

Each entry: what was decided, why, and what would reverse it.

---

### D1 — Repository lives at `MOBO Program/fred-mobo/`, remote is `FrEDMOBOExperimetation`

§9.3 calls for a separate repo named `fred-mobo`. The local directory uses that name; the GitHub
remote the user supplied is `github.com/JCSaishio/FrEDMOBOExperimetation`, so the two names differ.
The reference materials that are *not* deliverables — `context/` and `FrED_MOBO_Open_Items.docx` —
deliberately stay **outside** the repo, one level up, so the repo contains only the software and
its own documentation. `ARCHITECTURE.pdf` and the example CSV are copied in, as §9.3 requires, so
a clone is self-contained.

*Reverses if:* the user wants the whole `MOBO Program` folder to be the repo root.

---

### D2 — `fred_experiment_withgraphing.csv` is a schema fixture, not an acceptance fixture

§9.4's M2 acceptance numbers (onset 147.5 s, `N = 193`, `ρ̂₁ ≈ 0.90`, `N_eff ≈ 10`) describe
`fred_experiment_test.csv`, which is not in hand. The file supplied instead was recorded with
untuned heater gains, confirmed by the user on 21 Sep 2026, and measures differently: 7,729 rows,
526 distinct readings, `ρ̂₁ = 0.974`, `N_eff = 7.0`, no declared failure, and a 60 s ramp rather
than steady state.

It is therefore committed as a **format and schema reference only** — column names, `;` separator,
decimal comma, row shape — and no test asserts its numbers. Two properties measured from it *are*
instrument characteristics and do carry over, and are recorded because they constrain the model:

- Diameter is quantised on a **5.3 µm lattice** (33 distinct values; every gap an integer multiple
  of 5.3 µm). Within-run SE cannot go below ~1.5 µm and `f₁` cannot resolve finer than one step.
- The temperature channel drops out on ~4.5 % of rows (347 of 7,729 outside 70–110 °C on a 90 °C
  set-point).

*Reverses if:* the real `fred_experiment_test.csv`, or any run with a declared failure, arrives.

---

### D3 — Temperature values outside a plausibility range are masked, and the mask is surfaced

§2.3 states the extractor "never corrects, masks or models the temperature signal", and Algorithm 1
step 2 defines a plausibility mask for **diameter only**. The supplied file has 347 rows between
55.2 °C and 162.4 °C on a 90 °C set-point — physically impossible for the heater, so sensor
drop-outs rather than thermal excursions.

Decision, agreed with the user on 21 Sep 2026: extend step 2's "physically impossible values only"
principle to temperature and mask them, **but** the masked-row count and range are shown at intake
and carried into the export, so the instrument fault stays visible to the hardware side rather than
being silently cleaned away. This preserves the intent of §2.3 — no correcting, no modelling, no
interpolation — while keeping a broken sensor from poisoning the achieved-temperature diagnostic.

The numeric range is **open item E5** and is not yet chosen. Until it is, the mask is a no-op.

*Reverses if:* the user decides raw temperature should pass through untouched.

---

### D4 — PySide6 is commented out of `environment.yml` until M8

§9.2 item 11 forbids any UI until the backend runs end-to-end from the CLI, and §9.4 puts the UI at
M8. Installing a ~100 MB Qt binding that nothing imports for seven milestones would slow every CI
run and every fresh env create for no benefit. The pin is written and commented, so enabling it is
uncommenting one line.

*Reverses at:* the start of M8.

---

### D5 — Git identity set repo-locally; nothing pushed yet

The machine had no global `user.name` or `user.email`. Rather than set a global identity on the
user's behalf, it is set with `git config --local` inside this repo only, from the details already
known for this project. `gh` was not authenticated when M0 was built, so M0 is committed locally
and unpushed; the remote is still empty.

*Reverses if:* the user wants different authorship on a public repo — the commits are local and can
be amended freely until the first push.

---

### D6 — A `pyproject.toml` was added, which §9.3 does not list

Tests import `fred_mobo`, which needs the package root on `sys.path`. §9.3's layout omits any
packaging file. The smallest thing that works is a `pyproject.toml` carrying
`[tool.pytest.ini_options] pythonpath = ["."]` plus minimal project metadata — smaller than a
`conftest.py` path hack and standard enough that no reader will be surprised. It adds no build
step and no dependency.

*Reverses if:* the user prefers an editable install or a `conftest.py`.

---

### D7 — A short `README.md` was added, which §9.3 does not list

The remote is a **public** repo. A public repo with no README gives a visitor nothing. The README
is deliberately thin: what the project is, how to create the env, how to run the tests, and a
pointer to `docs/ARCHITECTURE.pdf`. Per §9.3's spirit it claims **no results the repo has not
produced**.

*Reverses if:* the user wants the repo to carry no README until there is something to report.

---

### D8 — `ℓ_f = π·11 mm = 34.558 mm/rev`, replacing the record's 50.27 mm/rev

The record (§1.1, §2.3) gives `ℓ_f = 50.27 mm/rev` "measured with a vernier" and hence
`v_f = 15.1 mm/min` at `ω_f = 0.30 RPM`. The user corrected this on 21 Sep 2026 (open item A4):
the extruder drive head is 11 mm in diameter, and under the no-slip assumption the advance per
revolution is its circumference, `π·11 = 34.558 mm`. So `v_f = 10.37 mm/min`. Applied in
`DeviceConfig.l_f_mm_per_rev`; every draw-ratio figure in the open-items document uses it.

It is still a *calculated* value. Two checks are pending in A4: that 0.30 RPM is the head's own
speed (after any gearbox), and that 11 mm is the gripping diameter rather than the outer diameter.
The marked-preform advance over N revolutions would settle both, slip included.

*Reverses if:* that measurement disagrees with 34.56 mm/rev by more than a few percent.

---

### D9 — Mode PX is removed; mode PM is the only power source *(pending confirmation, open item G2)*

§2.4 builds both sources and records which one each run used; §9.5 says the first campaign runs in
PX/B. On 21 Sep 2026 the user answered B5: "don't do the proxy anymore, just the measured power",
and B1: the PCB will "most likely" exist at campaign start. Consequences: B2, B3, B4 (every PX
constant) are closed as moot; the `PowerConfig` PX fields and `is_complete()` will be removed
rather than left as dead paths; the emulator writes one power-log format — the one specified in
`docs/POWER_LOG_REQUIREMENTS.docx` — which is also what the intake is tested against.

The risk is stated in the open-items document (G2): if the PCB is late, `f₂` cannot be computed
and the campaign cannot start; there is no bridge. This contradicts the record, so it is **not
applied to code until the user confirms G2**. The config still accepts `source = "PX"` today.

*Reverses if:* the user does not confirm G2, or the PCB slips past the retuned device.

---

### D10 — Spool geometry from A3 recorded; the draw ratio waits for G1, not for a measurement

A3 (21 Sep 2026): the spool core is 15 mm bare; fully wound it is about 33 mm, over a 20 mm
reciprocating traverse; "an estimate for now". With D8, the reference run's 0.48 mm plateau at
30 RPM implies `D_eff ≈ 23 mm` — inside that range, so the physics reconciles.

But the same kinematics say the fill is first-order: at 30 RPM, `R = 136` on the bare core and
`R = 300` when full, and a 180 s run adds ~2 mm of diameter (90 turns, ~42 turns per layer,
~2 layers), so the spool fills in ~9 runs. §4.2's "R is a known, exact function of the set-point
ω_s" therefore does not hold on this device. Whether the GP input is `ω_s` (spool controlled) or
`R` (wound diameter entered per run, `ω_s` derived from it) is a change to §1.1 and is put to the
user as open item G1 with a recommendation (R). `space.draw_ratio` and `linear_constraints` stay
`NotImplementedError`, now naming G1. `DeviceConfig.d_spool_mm` keeps its meaning as the bare
core; the full diameter and traverse are recorded here rather than in config until G1 decides
whether they are constants or per-run inputs.

*Reverses if:* G1 is answered — then this becomes an implementation, not a decision.
