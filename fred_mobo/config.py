"""Typed campaign configuration.

Holds every numeric the campaign runs on. Per §9.2 item 7 *everything* here is an
operator-editable default with one exception: ``n_0 = 2(d+1)`` is fixed and therefore derived,
not stored. The kernel choice locks after the first adaptive run is accepted.

Dimension-agnostic by construction (§7.4): variables and objectives are *lists*, so the 2D -> 3D
extension is a config change rather than a code path.

Implements: §1.1 (what is optimized), §9.2 item 7, §7.4 (extension to 3D)
Public interface (§7.1): ``CampaignConfig``, ``load``, ``save``
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "Variable",
    "Objective",
    "ConstraintConfig",
    "KernelConfig",
    "StoppingConfig",
    "DeviceConfig",
    "ExtractionConfig",
    "PowerConfig",
    "CampaignConfig",
    "load",
    "save",
    "ConfigError",
]

SCHEMA_VERSION = 1

POWER_LOG_COLUMNS: dict[str, str] = {
    "time_s": "Time (s)",
    "heater_v": "Heater voltage (V)",
    "heater_a": "Heater current (A)",
    "spooler_v": "Spooler voltage (V)",
    "spooler_a": "Spooler current (A)",
    "extruder_v": "Extruder voltage (V)",
    "extruder_a": "Extruder current (A)",
    "event": "Event",
}
"""Role → header name, exactly as docs/POWER_LOG_REQUIREMENTS.docx F2 specifies them."""

ConstraintMode = Literal["A", "B"]
KernelForm = Literal["matern52", "rbf"]
PowerSource = Literal["PM"]
"""Only PM (the PCB's own V·I log). Mode PX was removed on the user's instruction, open items
B5/G2, 21 Sep 2026 (DECISIONS D9). Kept as a Literal because ``power_source`` is still a
per-run column of the record's schema (§6.1)."""


class ConfigError(ValueError):
    """A campaign configuration failed validation."""


# --------------------------------------------------------------------------------------------
# Design variables and objectives — lists, so that d and M are not baked in (§7.4)
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Variable:
    """One design variable, in raw engineering units.

    ``log_scale`` marks a variable the 3D rotated coordinates of §7.4 treat logarithmically. It
    is carried here so the coordinate map can stay dimension-agnostic; it has no effect in 2D.
    """

    name: str
    label: str
    units: str
    lower: float
    upper: float
    log_scale: bool = False

    def validate(self) -> None:
        if not self.name:
            raise ConfigError("variable name must not be empty")
        if not (self.lower < self.upper):
            raise ConfigError(
                f"variable {self.name!r}: lower ({self.lower}) must be < upper ({self.upper})"
            )
        if self.log_scale and self.lower <= 0.0:
            raise ConfigError(
                f"variable {self.name!r}: log_scale requires a strictly positive lower bound, "
                f"got {self.lower}"
            )


@dataclass(frozen=True)
class Objective:
    """One objective, in raw engineering units and its natural direction.

    ``minimize`` records the direction the paper reports in. The negation for BoTorch happens at
    the boundary (§8), never here — this module always describes the problem in 'minimize' form.

    ``ideal`` and ``nadir`` are the fixed pre-campaign normalization range of §5.1. They are set
    from pilot ranges and must not be recomputed from campaign data.
    """

    name: str
    label: str
    units: str
    ref_point: float
    ideal: float
    nadir: float
    minimize: bool = True

    def validate(self) -> None:
        if not self.name:
            raise ConfigError("objective name must not be empty")
        if self.minimize:
            if not (self.ideal < self.nadir):
                raise ConfigError(
                    f"objective {self.name!r} is minimized, so ideal ({self.ideal}) must be "
                    f"< nadir ({self.nadir})"
                )
            if not (self.ref_point > self.ideal):
                raise ConfigError(
                    f"objective {self.name!r}: reference point ({self.ref_point}) must be worse "
                    f"than ideal ({self.ideal}); outcomes worse than the reference are worthless"
                )
        else:
            if not (self.ideal > self.nadir):
                raise ConfigError(
                    f"objective {self.name!r} is maximized, so ideal ({self.ideal}) must be "
                    f"> nadir ({self.nadir})"
                )
            if not (self.ref_point < self.ideal):
                raise ConfigError(
                    f"objective {self.name!r}: reference point ({self.ref_point}) must be worse "
                    f"than ideal ({self.ideal})"
                )

    def normalize(self, value: float) -> float:
        """Map a raw objective value onto the fixed affine scale of §5.1."""
        return (value - self.ideal) / (self.nadir - self.ideal)


# --------------------------------------------------------------------------------------------
# Sub-configurations
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstraintConfig:
    """Section C. One outcome column plus two thresholds — the same code path in both modes.

    Mode B (default, available today): the band is on the modeled diameter. Mode A (needs the
    spooler current channel): the band is on mean armature current, and declared failures
    contribute their margin.

    Either threshold may be ``None``, meaning that side is unbounded. ``lower``/``upper`` are the
    ``tau_lo``/``tau_hi`` of equations (10)-(11).
    """

    mode: ConstraintMode = "B"
    outcome: str = "diameter_mm"
    lower: float | None = None
    upper: float | None = None
    delta_t_c: float = 1.0
    """Temperature neighbourhood for the R-band of §4.2: nearby temperatures share a band.

    The record's default is 5 °C. The user set 1 °C on 21 Sep 2026 (open item E4, reaffirmed
    after push-back): a 1 °C change alters the melt's viscosity enough that a failure at 96 °C
    should not constrain 94 °C. Consequence, recorded in DECISIONS D12: with ~26 runs the
    neighbourhood will rarely contain a declared failure, so the R-band suggestion seldom fires
    and feasibility rests mainly on the diameter band. Editable at any time.
    """

    def validate(self) -> None:
        if self.mode not in ("A", "B"):
            raise ConfigError(f"constraint mode must be 'A' or 'B', got {self.mode!r}")
        if not self.outcome:
            raise ConfigError("constraint outcome column must be named")
        if self.lower is None and self.upper is None:
            raise ConfigError("constraint needs at least one of lower/upper")
        if self.lower is not None and self.upper is not None and not (self.lower < self.upper):
            raise ConfigError(
                f"constraint band is empty: lower ({self.lower}) >= upper ({self.upper})"
            )
        if self.delta_t_c <= 0:
            raise ConfigError("delta_t_c must be positive")


@dataclass(frozen=True)
class KernelConfig:
    """Section B.2. Set explicitly so that what the paper states is what runs.

    Matern-5/2 by default: it assumes only twice-differentiable sample paths, a weaker and more
    defensible smoothness claim near a failure boundary than the infinitely-smooth SE. The SE
    option lets the operator test that claim.

    ``locked`` becomes True when the first adaptive run is accepted (§3.2, §9.2 item 7). Before
    the lock a switch refits from scratch and is logged.
    """

    form: KernelForm = "matern52"
    ard: bool = True
    locked: bool = False

    def validate(self) -> None:
        if self.form not in ("matern52", "rbf"):
            raise ConfigError(f"kernel form must be 'matern52' or 'rbf', got {self.form!r}")
        if not self.ard:
            raise ConfigError("ARD-free kernels are not allowed (§9.8)")


@dataclass(frozen=True)
class StoppingConfig:
    """Section D.4. Convergence signals (15)-(17)."""

    delta_hv: float = 0.02
    """(15): relative hypervolume growth below which the observed front has stopped growing."""
    epsilon: float = 0.01
    """(16): fraction of current HV the best candidate must be unable to beat."""
    k: int = 3
    """Consecutive iterations (15) and (16) must both hold."""
    budget: int = 20
    """(17): adaptive runs after the initial design. Declared failures do not count (§1.3 x)."""

    def validate(self) -> None:
        if not (0.0 < self.delta_hv < 1.0):
            raise ConfigError(f"delta_hv must be in (0, 1), got {self.delta_hv}")
        if not (0.0 < self.epsilon < 1.0):
            raise ConfigError(f"epsilon must be in (0, 1), got {self.epsilon}")
        if self.k < 1:
            raise ConfigError(f"k must be >= 1, got {self.k}")
        if self.budget < 1:
            raise ConfigError(f"budget must be >= 1, got {self.budget}")


@dataclass(frozen=True)
class DeviceConfig:
    """Measured device constants (§1.1), as answered in the open-items document on 21 Sep 2026.

    ``d_spool_mm`` is the *bare core* diameter (open item A3). The wound diameter grows to about
    33 mm when full and the spool fills in roughly nine runs, so R at a fixed set-point varies by
    a factor 2.2 over a campaign. Which variable the GP sees, and how the per-run diameter is
    recorded, is open item G1; until it is decided nothing in this package computes a draw ratio
    from these values (DECISIONS D10).

    ``l_f_mm_per_rev`` is the circumference of the 11 mm extruder drive head, π·11 = 34.558 mm,
    under the no-slip assumption (A4; DECISIONS D8). It replaces the 50.27 mm/rev of the record.
    So ``v_f = l_f · omega_f = 10.37 mm/min`` at 0.30 RPM, not the 15.1 mm/min written in §2.3.

    ``d_in_mm`` = 7 mm is confirmed (A1) and is used by the emulator at M3.
    """

    d_spool_mm: float = 15.0
    l_f_mm_per_rev: float = 34.558
    omega_f_rpm: float = 0.30
    d_in_mm: float = 7.0

    def validate(self) -> None:
        for name in ("d_spool_mm", "l_f_mm_per_rev", "omega_f_rpm", "d_in_mm"):
            if getattr(self, name) <= 0:
                raise ConfigError(f"device constant {name} must be positive")


@dataclass(frozen=True)
class ExtractionConfig:
    """Section A defaults (§2.3), with the values the user set on 21 Sep 2026.

    ``d_star_mm`` = 0.40 mm is the first target session (open item E1).

    Two temperature masks implement DECISIONS D3/D13 — both drop rows before the achieved-mean
    diagnostic is computed, both surface their counts, neither touches the diameter statistics:

    * ``temp_plausible_c``: absolute range applied to the whole trace. Outside it a reading
      cannot be the block at all (below a lab's ambient, or above the 150 °C machine safety
      limit plus margin), so it is the sensor.
    * ``temp_setpoint_tolerance_c``: applied inside the steady-state window only. A reading more
      than this far from the set-point during the plateau is attributed to the sensor, not the
      heater (the user's 10 °C, open item E5). It is not applied outside the window, where the
      warm-up transient is legitimately far from the set-point.

    No low-pass filter is applied (asked in E5): the window mean already is one, a linear filter
    would not change it, and §2.3 forbids modelling the signal. The plateau standard deviation is
    reported instead so the noise level stays visible.

    ``delta_t_warn_c`` = 3 °C: intake warns when |T_achieved − T_setpoint| exceeds it (§2.3; E4).
    """

    d_star_mm: float = 0.40
    guard_s: float = 5.0
    w_min_s: float = 30.0
    d_plausible_mm: tuple[float, float] = (0.05, 2.0)
    temp_plausible_c: tuple[float, float] | None = (0.0, 160.0)
    temp_setpoint_tolerance_c: float | None = 10.0
    delta_t_warn_c: float | None = 3.0

    def validate(self) -> None:
        if self.d_star_mm <= 0:
            raise ConfigError("d_star_mm must be positive")
        if self.guard_s <= 0 or self.w_min_s <= 0:
            raise ConfigError("guard_s and w_min_s must be positive")
        lo, hi = self.d_plausible_mm
        if not (lo < hi):
            raise ConfigError(f"d_plausible_mm must be ordered, got {self.d_plausible_mm}")
        if not (lo <= self.d_star_mm <= hi):
            raise ConfigError(
                f"d_star_mm ({self.d_star_mm}) lies outside the plausibility range "
                f"{self.d_plausible_mm}"
            )
        if self.temp_plausible_c is not None:
            tlo, thi = self.temp_plausible_c
            if not (tlo < thi):
                raise ConfigError(f"temp_plausible_c must be ordered, got {self.temp_plausible_c}")
        if self.temp_setpoint_tolerance_c is not None and self.temp_setpoint_tolerance_c <= 0:
            raise ConfigError("temp_setpoint_tolerance_c must be positive")
        if self.delta_t_warn_c is not None and self.delta_t_warn_c <= 0:
            raise ConfigError("delta_t_warn_c must be positive")

    def diameter_band(self) -> tuple[float, float]:
        """Mode-B outcome constraint: 0.6 d* to 1.6 d* by default (§4.2)."""
        return (0.6 * self.d_star_mm, 1.6 * self.d_star_mm)


@dataclass(frozen=True)
class PowerConfig:
    """Section A.4. Mode PM only, and the column mapping for the PCB's power log.

    The defaults are the names, dialect and markers of ``docs/POWER_LOG_REQUIREMENTS.docx``
    (F1, F2, F6), which is also the format the emulator writes and ``data/examples/
    power_log_example.csv`` shows. HARDWARE-UNVALIDATED (§9.5): the real board's file may still
    differ, which is why every one of these is a config value and none is hard-coded — a schema
    change is a config edit plus one fixture update.

    ``columns`` maps the software's role names to the file's header strings. All seven roles
    must be present; ``validate`` refuses a mapping that drops one, because a missing voltage
    would silently turn a power into a current.
    """

    source: PowerSource = "PM"
    columns: dict[str, str] = field(default_factory=lambda: dict(POWER_LOG_COLUMNS))
    separator: str = ";"
    decimal: str = ","
    run_start_marker: str = "RUN_START"
    run_stop_marker: str = "RUN_STOP"
    offset_s: float = 0.0

    def validate(self) -> None:
        if self.source != "PM":
            raise ConfigError(
                f"power source must be 'PM' (mode PX was removed, DECISIONS D9), got {self.source!r}"
            )
        missing = [role for role in POWER_LOG_COLUMNS if role not in self.columns]
        if missing:
            raise ConfigError(f"power column mapping is missing roles {missing}")
        if not self.separator or not self.decimal or self.separator == self.decimal:
            raise ConfigError("power log separator and decimal must be distinct and non-empty")
        if not self.run_start_marker or not self.run_stop_marker:
            raise ConfigError("power log run markers must be non-empty")


# --------------------------------------------------------------------------------------------
# The campaign configuration
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CampaignConfig:
    """Everything one campaign runs on. JSON round-trips exactly (§9.4 M1)."""

    variables: list[Variable]
    objectives: list[Objective]
    constraint: ConstraintConfig = field(default_factory=ConstraintConfig)
    kernel: KernelConfig = field(default_factory=KernelConfig)
    stopping: StoppingConfig = field(default_factory=StoppingConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    power: PowerConfig = field(default_factory=PowerConfig)
    q: int = 1
    mc_samples: int = 128
    num_restarts: int = 10
    raw_samples: int = 512
    seed: int = 0
    schema_version: int = SCHEMA_VERSION

    # ---------------------------------------------------------------- derived

    @property
    def d(self) -> int:
        """Number of design variables."""
        return len(self.variables)

    @property
    def m(self) -> int:
        """Number of objectives."""
        return len(self.objectives)

    @property
    def n_initial(self) -> int:
        """``n_0 = 2(d + 1)`` Sobol points.

        Derived rather than stored: §9.2 item 7 makes this the one numeric the operator may not
        edit, and a property cannot be edited into an inconsistent state.
        """
        return 2 * (self.d + 1)

    # ---------------------------------------------------------------- validation

    def validate(self) -> CampaignConfig:
        """Raise ``ConfigError`` on anything inconsistent. Returns self so it can be chained."""
        if not self.variables:
            raise ConfigError("a campaign needs at least one design variable")
        if len(self.objectives) < 2:
            raise ConfigError(
                f"this is a multi-objective campaign; got {len(self.objectives)} objective(s)"
            )

        for v in self.variables:
            v.validate()
        for o in self.objectives:
            o.validate()

        for group, names in (
            ("variable", [v.name for v in self.variables]),
            ("objective", [o.name for o in self.objectives]),
        ):
            if len(set(names)) != len(names):
                raise ConfigError(f"duplicate {group} names: {names}")

        self.constraint.validate()
        self.kernel.validate()
        self.stopping.validate()
        self.device.validate()
        self.extraction.validate()
        self.power.validate()

        if self.q < 1:
            raise ConfigError(f"q must be >= 1, got {self.q}")
        if self.mc_samples < 1:
            raise ConfigError(f"mc_samples must be >= 1, got {self.mc_samples}")
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigError(
                f"config schema version {self.schema_version} != {SCHEMA_VERSION}; migrate first"
            )
        return self

    def with_kernel_locked(self) -> CampaignConfig:
        """Return a copy with the kernel locked, as the first accepted adaptive run requires."""
        return replace(self, kernel=replace(self.kernel, locked=True))

    # ---------------------------------------------------------------- JSON round-trip

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CampaignConfig:
        def _tuple_or_none(value: Any) -> tuple[float, float] | None:
            return None if value is None else (float(value[0]), float(value[1]))

        power_raw = dict(raw.get("power", {}))

        extraction_raw = dict(raw.get("extraction", {}))
        if "d_plausible_mm" in extraction_raw:
            extraction_raw["d_plausible_mm"] = _tuple_or_none(extraction_raw["d_plausible_mm"])
        if "temp_plausible_c" in extraction_raw:
            extraction_raw["temp_plausible_c"] = _tuple_or_none(extraction_raw["temp_plausible_c"])

        return cls(
            variables=[Variable(**v) for v in raw["variables"]],
            objectives=[Objective(**o) for o in raw["objectives"]],
            constraint=ConstraintConfig(**raw.get("constraint", {})),
            kernel=KernelConfig(**raw.get("kernel", {})),
            stopping=StoppingConfig(**raw.get("stopping", {})),
            device=DeviceConfig(**raw.get("device", {})),
            extraction=ExtractionConfig(**extraction_raw),
            power=PowerConfig(**power_raw),
            q=raw.get("q", 1),
            mc_samples=raw.get("mc_samples", 128),
            num_restarts=raw.get("num_restarts", 10),
            raw_samples=raw.get("raw_samples", 512),
            seed=raw.get("seed", 0),
            schema_version=raw.get("schema_version", SCHEMA_VERSION),
        )

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> CampaignConfig:
        return cls.from_dict(json.loads(text))


def save(config: CampaignConfig, path: str | Path) -> Path:
    """Write ``config`` to ``path`` as JSON. Validates first — never persist a broken config."""
    config.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.to_json(), encoding="utf-8")
    return path


def load(path: str | Path) -> CampaignConfig:
    """Read a campaign config from JSON and validate it."""
    return CampaignConfig.from_json(Path(path).read_text(encoding="utf-8")).validate()


# --------------------------------------------------------------------------------------------
# The phase-2D default campaign
# --------------------------------------------------------------------------------------------


def default_2d_campaign(d_star_mm: float = 0.40) -> CampaignConfig:
    """The phase-2D campaign of §1.1, with the defaults as they stand after the 21 Sep 2026 answers.

    Temperature box [90, 130] °C, not the record's [70, 100]: the EVA feedstock does not draw
    below 90 °C and the machine's safety limit is 150 °C (open item A2; DECISIONS D11). The user
    widened the upper bound from the provisional 120 °C to 130 °C in the Rev. 5 reply.

    The power objective's reference point, ideal and nadir are placeholders: §5.1 freezes the
    power side at 'worst pilot value + 10 %' after the first PM pilot, which has not been run.
    The error side, 0.15 mm, was confirmed on 21 Sep 2026 (open item E3).
    """
    band_lo, band_hi = ExtractionConfig(d_star_mm=d_star_mm).diameter_band()
    return CampaignConfig(
        variables=[
            Variable("T", "heater temperature set-point", "degC", 90.0, 130.0),
            Variable("omega_s", "spooler speed set-point", "RPM", 25.0, 50.0),
        ],
        objectives=[
            Objective(
                name="diameter_error",
                label="steady-state diameter error |d - d*|",
                units="mm",
                ref_point=0.15,
                ideal=0.0,
                nadir=0.15,
            ),
            Objective(
                name="power",
                label="mean total actuator power",
                units="W",
                ref_point=100.0,
                ideal=0.0,
                nadir=100.0,
            ),
        ],
        constraint=ConstraintConfig(mode="B", outcome="diameter_mm", lower=band_lo, upper=band_hi),
        extraction=ExtractionConfig(d_star_mm=d_star_mm),
    )
