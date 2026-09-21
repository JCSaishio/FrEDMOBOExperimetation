# fred-mobo

Constrained two-objective Bayesian optimization for **FrED**, a fiber-extrusion testbed at
Grupo Estudiantil FrED, Tecnológico de Monterrey, Campus Ciudad de México.

A local desktop application that runs a multi-objective BO campaign on the device: the operator
runs an experiment, uploads the log, declares whether the run failed, and the app proposes the
next set-point. The campaign output is a Pareto front plus a set of exported maps that a
downstream supervisory agent can operate from.

> **Status: scaffold (M0).** No optimization logic is implemented yet. Nothing in this repository
> has produced a result, and no result is claimed here.

## The problem

| | | |
|---|---|---|
| **Design variables** | heater temperature set-point `T` | 70 – 100 °C |
| | spooler speed set-point `ω_s` | 25 – 50 RPM |
| **Objectives** *(both minimized)* | `f₁ = \|d − d*\|` steady-state diameter error | mm |
| | `f₂ = P` mean total actuator power | W |

Extrusion speed is held constant in this phase, so the draw ratio `R = v_s/v_f` is a known
function of the spooler set-point. Two failure modes bracket it — breakage at high `R`, overflow
at low `R` — and are handled as a learned outcome constraint rather than a hard bound, because
where the boundaries sit, and how they move with temperature, is exactly what is unknown.

The acquisition function is **qLogNEHVI**. Objectives are negated internally (BoTorch maximizes),
the hypervolume reference point is fixed before the campaign and never recomputed from data, and
the final Pareto set is recommended from the posterior mean rather than from raw observations.

## Specification

The full specification — mathematics, data reduction, constraint handling, convergence rule,
export format and module boundaries — is **`docs/ARCHITECTURE.pdf`** (architecture record v1.4).
Every equation in it carries a source. This repository implements that document; it does not
redesign it.

- `docs/PLAN.md` — milestones M0–M10, each with its acceptance test
- `docs/PROGRESS.md` — session log and the current resume point
- `docs/DECISIONS.md` — choices made where the record is silent, and any deviation from it

## Setup

Miniforge rather than Anaconda, and BoTorch by pip inside the conda env — it stopped publishing
to the `pytorch` conda channel after v0.12.

```bash
conda env create -f environment.yml
conda activate fred-mobo
pytest
```

## Repository layout

```
fred_mobo/      config  space  extraction  power  models  constraints
                acquisition  pareto  storage  campaign  simulate  export
                ui/         PySide6 windows (milestone M8)
scripts/        run_campaign_cli.py  make_example_campaign.py
tests/          one module per milestone acceptance test
docs/           ARCHITECTURE.pdf  PLAN.md  PROGRESS.md  DECISIONS.md
data/examples/  device-log schema reference
```

## A note on the example CSV

`data/examples/` carries a device log so the column schema is self-contained — semicolon
separator, decimal comma, ~43 Hz logging against a ~3 Hz vision update. It is a **format
reference only**: it was recorded with untuned heater gains and contains no declared failure, so
no test asserts its values. See `docs/DECISIONS.md` D2.

## Hardware status

The power-measurement PCB does not exist yet. Until it does, the power objective is computed from
a proxy (mode PX) and the constraint runs on declared failures plus a diameter band (mode B). The
mode PM and mode A code paths are built and tested against the emulator only, and are marked
hardware-unvalidated in `docs/DECISIONS.md`.

## License

Not yet chosen.
