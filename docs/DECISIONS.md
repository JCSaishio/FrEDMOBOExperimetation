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

### D9 — Mode PX is removed; mode PM is the only power source *(CONFIRMED by the user, G2, 21 Sep 2026)*

§2.4 builds both sources and records which one each run used; §9.5 says the first campaign runs in
PX/B. On 21 Sep 2026 the user answered B5: "don't do the proxy anymore, just the measured power",
and B1: the PCB will "most likely" exist at campaign start. Consequences: B2, B3, B4 (every PX
constant) are closed as moot; the `PowerConfig` PX fields and `is_complete()` will be removed
rather than left as dead paths; the emulator writes one power-log format — the one specified in
`docs/POWER_LOG_REQUIREMENTS.docx` — which is also what the intake is tested against.

The risk is stated in the open-items document (G2): if the PCB is late, `f₂` cannot be computed
and the campaign cannot start; there is no bridge. The user confirmed G2 with "Yes". Applied:
`PowerSource = Literal["PM"]`; the PX fields, `is_complete` and the calibration table are gone
from `PowerConfig`; the column mapping, dialect and run markers default to the requirements file
(`POWER_LOG_COLUMNS`) and `validate` refuses a mapping that drops a role. G3 ("PM/B for the first
campaign, mode A parked") was confirmed in the same round; mode A stays a config option only.

*Reverses if:* the PCB slips past the retuned device and a bridge is needed after all.

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

**Amended after the Rev. 3 replies (21 Sep 2026).** Two facts and one correction: the spool *is
emptied between runs*; the user prefers `ω_s`; and the fill per run does **not** depend on the
set-point — `ΔD = 2·t·d_in²·v_f/(π·D·w)` with `w = 20 mm` the traverse, i.e. `48.5/D` mm per
180 s run at `ω_f = 0.30` (+3.23 mm on the bare core at 25 RPM and at 50 RPM alike, checked
numerically). So under an "empty before every run, same run length" protocol the spool is in the
same state for every run and `R` is again a fixed function of `ω_s`, through the mid-run diameter
`D_mid = D_core + ΔD/2 ≈ 16.6 mm`. The recommendation put to the user is therefore **reversed to
option A (keep `ω_s`, formalise the protocol)**, with A+ (a ~33 mm sleeve, which cuts the
within-run drift from +22 % to +4 % in R and puts 0.40 mm mid-box at `ω_f = 0.30`) and B (R as the
variable, per-run measurement) as the alternatives. The "implied `D_eff ≈ 23 mm`" inference from
the sample file is **withdrawn** — the user states its sensor was uncalibrated. Open item H1 (three
calibration runs with a micrometer) is proposed to measure `d(ω_s)`, the effective `ℓ_f` and the
fill per run before anything is built on the kinematic table.

**Amended again after the saved Rev. 5 reply (22 Sep 2026).** The user answered G1 with a
*model* rather than a choice, and asked for the item to stay open:

> "…the amount of fiber in the spool is determined by the spooling speed, so I think that A would
> be okay but we could make a calculation about how much the spool has filled up using the spool
> speed and the amount of time elapsed and the average diameter of the fiber. For every revolution
> we can assume that the diameter in the spooled section increases by twice the average diameter
> of the fiber and that it will take the full length of the spool divided by the diameter
> revolutions to fill up the spool and update the tangential speed that the fiber experiences so
> what we should really standardize is the final dimeter of the spool after a run and this can be
> roughly estimated using mass conservation. Then the user can measure the spool and record the
> final height and I suppose that a correction could be made there although I will still need you
> to keep this item open so that we can discuss how this transfers to the points. So keep these
> items open and lets discuss how to expand A without the printed sleeve."

Their layer model **is** the square-packing model this decision already used, so it confirms the
arithmetic rather than replacing it; it is now written down properly as **D14**, together with the
finding that their stated premise — that the fill depends on the spooling speed — does not survive
their own equations. **A+ (the printed sleeve) is withdrawn**, at the user's instruction. G1
therefore stays **open**, narrowed to one question (how the spool state enters the design point,
and which sleeve-free lever puts `d* = 0.40 mm` inside the box), carried into Rev. 5 of the
open-items document.

*Reverses if:* G1 is answered — then this becomes an implementation, not a decision.

---

### D11 — Temperature box `[90, 130] °C`, replacing the record's `[70, 100]`

Open item A2 (21 Sep 2026): the feedstock is EVA hot-melt; it draws at 90 °C and not below; the
machine's safety limit is 150 °C. A box starting at 70 °C would spend most of the Sobol design
where nothing extrudes. The lower bound is the user's.

The upper bound was provisionally 120 °C (my proposal: the record's 30 °C span, 30 °C under the
safety limit). **Settled at 130 °C on 22 Sep 2026** by the A2 reply: *“I think wider could be
better although I am sure that at a certain temp the fiber will flow tool quickly for the motor
to handle so this 130 is fine.”* So the box is `[90, 130]` — a 40 °C span, still 20 °C under the
safety limit, with the E5 absolute guard at 160 °C unchanged so a runaway is still shown rather
than masked. Applied in `default_2d_campaign`; the emulator's `g(T)` will have no flow below
90 °C.

The user's own caveat — that above some temperature the melt flows faster than the spooler can
take up — is a *feasibility* statement, not a box statement: it is what the mode-B constraint
model is for. Runs at the hot end that break are declared failures at intake and teach the
classifier where the ceiling is; §4 does not need the box to exclude them in advance, and
narrowing the box to avoid them would hide the boundary the campaign is supposed to find.

*Reverses if:* the hot end turns out to break so often that the Sobol design wastes runs — then
the upper bound comes down and the reason is recorded here.

---

### D12 — R-band neighbourhood `δ_T = 1 °C`, not the record's 5 °C

§4.2 defaults the temperature neighbourhood of the mode-B R-band to 5 °C. The user set 1 °C
(open item E4) and, after push-back on the statistical consequence, reaffirmed it on physical
grounds: a 1 °C change alters the melt's viscosity enough that a failure at 96 °C should not
constrain 94 °C. Applied as `ConstraintConfig.delta_t_c = 1.0`.

Consequence, recorded so it is not a surprise: with ~26 runs over a 30 °C box and a handful of
declared failures, a ±1 °C neighbourhood will rarely contain one, so the R-band *suggestion* of
§4.2 will seldom fire and feasibility rests on the diameter-band outcome constraint and on the
declared failures being visible on the (T, R) map of §4.3. A one-sided neighbourhood (a failure at
`T_i` constraining only `T ≥ T_i` or only `T ≤ T_i`) would need no `δ_T` at all, but requires the
*direction* of the temperature effect on breakage, which open item H1 would measure.

*Reverses if:* failures near-repeat during the campaign and the user widens it (editable per
campaign).

---

### D13 — Two temperature masks, no low-pass filter (supersedes the "range" part of D3)

Open item E5 (21 Sep 2026). The user chose a ±10 °C attribution ("within 10 °C of the set-point
is the heater, beyond it the sensor") and suggested a low-pass filter. Applied:

- `temp_setpoint_tolerance_c = 10.0`: inside the steady-state window only, a row with
  `|T − T_sp| > 10 °C` is attributed to the sensor and dropped from the achieved-mean diagnostic.
  Not applied outside the window, where the warm-up transient is legitimately far from the
  set-point.
- `temp_plausible_c = (0, 160)`: absolute guard on the whole trace — below ambient or above the
  150 °C safety limit plus margin cannot be the block, wherever it happens. A runaway toward the
  limit is still shown, not masked.
- Both counts, and the plateau standard deviation of the temperature signal, are surfaced at intake
  and in the export (D3's principle).
- **No low-pass filter.** The window mean already is one (cut-off ≈ 0.03 Hz for a ≥ 30 s window at
  43 Hz), a linear filter would not change it measurably, §2.3 forbids modelling the temperature
  signal, and a filter would hide from the hardware side exactly the noise D1 asks them to look at.
  A display-only smoothing, if wanted, is a UI choice at M8 and changes no number.

On the untuned sample file the ±10 °C rule drops 728 of 5,138 window rows (14 %) because the loop
sat 5 °C below the set-point with 8 °C of noise on top; the window mean moves by 0.1 °C. After the
retune (D2) the share should fall to a few percent; if it does not, the count is the D1 signal.

*Reverses if:* the user wants the raw signal untouched, or a different tolerance.

---

### D14 — The spool-fill law, and `R` becomes `R(t)`

Settled by the Rev. 5 reply to G1 (22 Sep 2026). The user's winding model — one layer is `w/d`
turns laid side by side across the traverse, completing a layer raises the diameter by `2·d`, and
the fibre's tangential speed follows the growing `D` — is square packing of round turns, i.e. the
`π/4` already implicit in D10's `ΔD = 48.5/D`. It is adopted as the emulator's and the extractor's
model of the spool.

Integrating it forward in time (`scripts` not required; scratchpad `physics_g1_rev5.py`, forward
Euler at 10 ms, with no cancellation assumed):

```
dD/dt = ω_s · 2·d²/w        and        d = d_in·√(v_f / (π·D·ω_s))
⇒ dD/dt = 2·d_in²·v_f / (π·D·w)         — ω_s cancels
⇒ D_end² − D_start² = 4·d_in²·v_f·t / (π·w) = 97.02 mm²  for a 180 s run at ω_f = 0.30
```

| `D₀` | `ω_s` | `D_end` | `ΔD` | `d` start → end | drift |
|---|---|---|---|---|---|
| 15 mm | 25 RPM | 17.9449 mm | 2.9449 mm | 0.6567 → 0.6004 mm | −8.6 % |
| 15 mm | 30 RPM | 17.9449 mm | 2.9449 mm | 0.5994 → 0.5481 mm | −8.6 % |
| 15 mm | 37.5 RPM | 17.9449 mm | 2.9449 mm | 0.5362 → 0.4902 mm | −8.6 % |
| 15 mm | 50 RPM | 17.9449 mm | 2.9449 mm | 0.4643 → 0.4245 mm | −8.6 % |

Three consequences, all recorded here so they are not re-derived:

1. **The fill is set-point independent.** Spinning faster draws a proportionally thinner fibre, so
   the *volume* laid down per second is fixed by the extruder alone. The user's premise that "the
   amount of fiber in the spool is determined by the spooling speed" is the one part of the reply
   that does not hold — and it is good news, because their stated goal, *standardising the final
   spool diameter*, is then delivered for free by the protocol they already follow: empty the
   spool, keep the run length fixed, and `D_end = 17.9449 mm` on every run at every set-point.
2. **`R` is a function of time within a run, not a constant.** `R(t) = π·D(t)·ω_s / v_f`, so
   `space.draw_ratio` must expose the `D`-path, and `f₁`'s window mean is a mean over a drifting
   `d`. On the bare core that drift is 0.0514 mm across a run — **9.7 steps of the 5.3 µm vision
   lattice (D3)** — a clean monotone ramp, which is the signature Appendix A's trend check exists
   to catch. Left alone it would flag a large share of runs as non-steady.
3. **`D_start` and `D_end` are recorded per run, as a check, not as a GP input.** The user asked
   for the operator to "measure the spool and record the final height". Under the emptied-spool
   protocol the `D`-path is *deterministic and identical* for every run, so the spool state does
   not vary between design points and `ω_s` remains the coordinate; the vernier reading's job is
   to confirm the protocol held. A run whose measured `D_end` departs from 17.9449 mm is flagged,
   and its `R̄` recomputed from the measured path. This is the beginning of an answer to the user's
   "how this transfers to the points", and the rest is G1.

*Reverses if:* the protocol stops emptying the spool between runs — then `D_start` becomes a real
per-run covariate and the errors-in-variables problem the user is pointing at becomes live.

---

### D15 — H1 accepted, but it will be run on a *full* spool

The Rev. 5 reply to H1 (22 Sep 2026) accepts the calibration runs: *"I'll run those as soon as I
can with the full spool and vision system updated and Ii will also try to have the diameter as
constant as possible here."* Recorded, with three notes.

**A full spool cannot be the campaign protocol, only a calibration condition.** Pre-winding a bare
15 mm core to 33 mm costs 9 runs' worth of fibre; and a campaign *starting* at 33 mm would reach
`√(33² + 6·97.02) = 40.9 mm` after the Sobol block alone and 60.1 mm after 26 runs, against a
stated capacity of 33 mm. So the campaign still runs from the emptied core, and H1's numbers will
be taken at a spool state the campaign never sees.

**That does not spoil H1**, because what H1 is for is the constants, not the operating point: with
`D_start` and `D_end` on the vernier and a micrometer on the fibre, `ℓ_f` follows from mass
conservation at *any* `D`, as does the vision-minus-micrometer offset and the direction of the
temperature effect. It does mean the runs must record `D_start` and `D_end`, not just `ω_s` — the
intake fields below.

**What H1 will show on a full spool**, on today's constants, so the user can sanity-check the rig
before trusting it: `ω_s = 25 / 37.5 / 50 RPM → d = 0.4427 / 0.3615 / 0.3130 mm` at the start of
the run, with `d* = 0.40 mm` landing at `ω_s ≈ 30 RPM`. If the micrometer disagrees with these by
more than a few percent, `ℓ_f` is the constant at fault (D8, A4) — which is the whole point.

Their added intention, "have the diameter as constant as possible", is exactly the within-run
drift of D14: on a full spool it is −2.1 % rather than the bare core's −8.6 %, so this condition
will look better behaved than the campaign will.

*Reverses if:* the calibration is run on the bare core after all — the analysis is the same, the
recorded `D_start` simply differs.
