# fred-mobo

Constrained two-objective BO for the FrED fiber-extrusion testbed.
**Spec: `docs/ARCHITECTURE.pdf` (architecture record v1.4). Implement it; do not redesign it.**
Where it is silent: simplest option, record in `docs/DECISIONS.md`, continue.

**Stack** Python 3.12 · BoTorch 0.18.1 · GPyTorch 1.15.2 · PyTorch 2.13 · PySide6 (M8) · SQLite ·
pytest. `conda activate fred-mobo` (miniforge, not Anaconda). Pins in `environment.yml`.

## Non-negotiables (§9.2)

1. qLogNEHVI only; objectives negated internally; reference point fixed pre-campaign, normalized,
   never recomputed. `prune_baseline=True`, S=128 Sobol QMC, double precision.
2. Independent GPs via `ModelListGP`, explicit `ScaleKernel(MaternKernel(nu=2.5, ard))` or
   `ScaleKernel(RBFKernel(ard))` per config, `Standardize`, noise inferred. Refit from scratch
   every accepted run — no warm start, no pickled models.
3. Objective 1 is `|d - d*|` computed inside a `GenericMCMultiOutputObjective` on samples of `d`.
   The GP models `d`, never `|d - d*|` — a stationary kernel cannot represent the crease at `d*`.
4. Constraints are outcome callables (negative = feasible), two thresholds on one output,
   evaluated inside the MC expectation. **Never** multiply by a probability of feasibility.
5. Failures are declared by the operator. The software suggests, never decides.
6. Failed runs never enter the objective GPs; constraint GP only in mode A.
7. Everything numeric is an editable config default. `n_0 = 6` is the exception. Kernel locks
   after the first accepted adaptive run.
8. Target sessions share one dataset and one set of GPs; a new `d*` changes only the objective
   transform and the diameter band.
9. Save/resume: campaign folder (SQLite + config JSON + copied CSVs) is the only state.
10. **Never write a BoTorch/GPyTorch signature from memory.** Read the installed docstring first.
11. No UI until the backend runs end-to-end from the CLI on the emulator, all tests passing.

## Not allowed (§9.8)

No web server, Streamlit, cloud calls or Ax (raw BoTorch only — every step inspectable). No
automatic failure detection overriding the operator. No imputed values for failed runs. No
recomputed reference point. No ARD-free kernels. No invented citations or equations.

## Session protocol (§9.6)

Start: read `docs/PROGRESS.md`, run `pytest`, restate the next step in one line. Small commits.
After each unit of work update `PROGRESS.md` with what is done, which test verifies it, and where
to resume. Never leave a half-written function without a `TODO(resume)` plus a `PROGRESS.md` line.
