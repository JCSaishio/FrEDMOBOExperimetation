"""Acceptance tests for milestone M1 — config.

CampaignConfig JSON round-trip; validation rejects inconsistent configs.
"""

from __future__ import annotations

import json

import pytest

from fred_mobo.config import (
    CampaignConfig,
    ConfigError,
    ConstraintConfig,
    DeviceConfig,
    ExtractionConfig,
    POWER_LOG_COLUMNS,
    KernelConfig,
    Objective,
    PowerConfig,
    StoppingConfig,
    Variable,
    default_2d_campaign,
    load,
    save,
)


# ------------------------------------------------------------------ round-trip (the M1 criterion)


def test_json_round_trip_is_exact() -> None:
    """The stated M1 acceptance test: a config survives JSON unchanged."""
    original = default_2d_campaign()
    restored = CampaignConfig.from_json(original.to_json())
    assert restored == original


def test_round_trip_through_disk(tmp_path) -> None:
    original = default_2d_campaign(d_star_mm=0.42)
    path = save(original, tmp_path / "campaign" / "config.json")
    assert path.is_file()
    assert load(path) == original


def test_round_trip_preserves_optional_and_tuple_fields(tmp_path) -> None:
    """Tuples and None survive JSON, which turns tuples into lists if nothing converts them back."""
    original = CampaignConfig(
        variables=default_2d_campaign().variables,
        objectives=default_2d_campaign().objectives,
        constraint=ConstraintConfig(mode="A", outcome="spooler_current_a", lower=0.2, upper=1.1),
        extraction=ExtractionConfig(
            d_star_mm=0.35,
            temp_plausible_c=(20.0, 130.0),
            temp_setpoint_tolerance_c=None,
            delta_t_warn_c=2.5,
        ),
        power=PowerConfig(
            columns={**POWER_LOG_COLUMNS, "heater_a": "I_heater [A]"},
            separator=",",
            decimal=".",
            offset_s=1.25,
        ),
    )
    restored = CampaignConfig.from_json(original.to_json())
    assert restored == original
    assert restored.extraction.temp_plausible_c == (20.0, 130.0)
    assert restored.extraction.temp_setpoint_tolerance_c is None
    assert restored.power.columns["heater_a"] == "I_heater [A]"


def test_json_is_human_readable_and_sorted() -> None:
    """The campaign file is audited by hand, so it must not be a single line."""
    text = default_2d_campaign().to_json()
    assert "\n" in text
    parsed = json.loads(text)
    assert parsed["variables"][0]["name"] == "T"


# ------------------------------------------------------------------ derived quantities


def test_n_initial_is_two_d_plus_one() -> None:
    """§5.3: n_0 = 2(d+1) = 6 for d = 2, and §9.2 item 7 makes it the one non-editable numeric."""
    config = default_2d_campaign()
    assert config.d == 2
    assert config.n_initial == 6


def test_n_initial_follows_dimension_without_a_code_change() -> None:
    """§7.4: going to 3D must be a config change, not a code path."""
    base = default_2d_campaign()
    three_d = CampaignConfig(
        variables=[*base.variables, Variable("v_f", "feed speed", "mm/min", 10.0, 30.0)],
        objectives=base.objectives,
        constraint=base.constraint,
        extraction=base.extraction,
    )
    assert three_d.d == 3
    assert three_d.n_initial == 8


def test_n_initial_is_not_settable() -> None:
    with pytest.raises(TypeError):
        CampaignConfig(
            variables=default_2d_campaign().variables,
            objectives=default_2d_campaign().objectives,
            n_initial=99,  # type: ignore[call-arg]
        )


def test_m_counts_objectives() -> None:
    assert default_2d_campaign().m == 2


# ------------------------------------------------------------------ validation


def test_default_campaign_validates() -> None:
    assert default_2d_campaign().validate() is not None


def test_rejects_inverted_variable_bounds() -> None:
    with pytest.raises(ConfigError, match="must be <"):
        CampaignConfig(
            variables=[Variable("T", "heater", "degC", 100.0, 70.0)],
            objectives=default_2d_campaign().objectives,
        ).validate()


def test_rejects_single_objective() -> None:
    """This is a multi-objective campaign; a single objective is a configuration mistake."""
    with pytest.raises(ConfigError, match="multi-objective"):
        CampaignConfig(
            variables=default_2d_campaign().variables,
            objectives=default_2d_campaign().objectives[:1],
        ).validate()


def test_rejects_duplicate_variable_names() -> None:
    with pytest.raises(ConfigError, match="duplicate variable"):
        CampaignConfig(
            variables=[
                Variable("T", "heater", "degC", 70.0, 100.0),
                Variable("T", "also heater", "degC", 70.0, 100.0),
            ],
            objectives=default_2d_campaign().objectives,
        ).validate()


def test_rejects_reference_point_better_than_ideal() -> None:
    """§5.1: the reference point reads as 'outcomes worse than this are worthless'."""
    with pytest.raises(ConfigError, match="reference point"):
        Objective("e", "error", "mm", ref_point=-1.0, ideal=0.0, nadir=0.15).validate()


def test_rejects_ideal_worse_than_nadir_for_a_minimized_objective() -> None:
    with pytest.raises(ConfigError, match="ideal"):
        Objective("e", "error", "mm", ref_point=0.15, ideal=0.20, nadir=0.10).validate()


def test_rejects_ard_free_kernel() -> None:
    """§9.8 forbids ARD-free kernels outright."""
    with pytest.raises(ConfigError, match="ARD-free"):
        KernelConfig(ard=False).validate()


def test_rejects_unknown_kernel_form() -> None:
    with pytest.raises(ConfigError, match="kernel form"):
        KernelConfig(form="rq").validate()  # type: ignore[arg-type]


def test_rejects_empty_constraint_band() -> None:
    with pytest.raises(ConfigError, match="band is empty"):
        ConstraintConfig(lower=1.0, upper=0.5).validate()


def test_rejects_constraint_with_no_thresholds() -> None:
    with pytest.raises(ConfigError, match="at least one"):
        ConstraintConfig(lower=None, upper=None).validate()


def test_rejects_target_outside_plausibility_range() -> None:
    with pytest.raises(ConfigError, match="plausibility"):
        ExtractionConfig(d_star_mm=5.0).validate()


def test_rejects_nonpositive_device_constants() -> None:
    with pytest.raises(ConfigError, match="must be positive"):
        DeviceConfig(d_spool_mm=0.0).validate()


def test_rejects_out_of_range_stopping_parameters() -> None:
    with pytest.raises(ConfigError, match="delta_hv"):
        StoppingConfig(delta_hv=1.5).validate()
    with pytest.raises(ConfigError, match="k must be"):
        StoppingConfig(k=0).validate()


def test_save_refuses_to_persist_a_broken_config(tmp_path) -> None:
    """A broken config must never reach disk — resume would then load it back."""
    broken = CampaignConfig(variables=[], objectives=default_2d_campaign().objectives)
    with pytest.raises(ConfigError):
        save(broken, tmp_path / "config.json")
    assert not (tmp_path / "config.json").exists()


# ------------------------------------------------------------------ spec-specific behaviour


def test_kernel_locks_after_first_adaptive_run() -> None:
    """§3.2: the kernel locks once the first adaptive run is accepted."""
    config = default_2d_campaign()
    assert config.kernel.locked is False
    assert config.with_kernel_locked().kernel.locked is True
    assert config.kernel.locked is False, "with_kernel_locked must not mutate the original"


def test_diameter_band_defaults_to_the_spec_multiples() -> None:
    """§4.2: defaults 0.6 d* and 1.6 d*."""
    lo, hi = ExtractionConfig(d_star_mm=0.35).diameter_band()
    assert lo == pytest.approx(0.21)
    assert hi == pytest.approx(0.56)


def test_default_campaign_uses_mode_b_and_pm() -> None:
    """Open items G2/G3 (21 Sep 2026): the first campaign runs PM / mode B; PX was removed (D9)."""
    config = default_2d_campaign()
    assert config.constraint.mode == "B"
    assert config.power.source == "PM"


def test_power_columns_default_to_the_requirements_file_names() -> None:
    """docs/POWER_LOG_REQUIREMENTS.docx F2 names, F1 dialect, F6 markers — config, not hard-coded."""
    power = default_2d_campaign().power
    assert power.columns["heater_v"] == "Heater voltage (V)"
    assert power.columns["event"] == "Event"
    assert (power.separator, power.decimal) == (";", ",")
    assert (power.run_start_marker, power.run_stop_marker) == ("RUN_START", "RUN_STOP")


def test_power_mapping_must_name_every_role() -> None:
    """A dropped voltage column would silently turn a power into a current."""
    columns = dict(POWER_LOG_COLUMNS)
    del columns["spooler_v"]
    with pytest.raises(ConfigError, match="spooler_v"):
        PowerConfig(columns=columns).validate()


def test_px_is_no_longer_a_valid_power_source() -> None:
    """DECISIONS D9, confirmed by the user in open item G2."""
    with pytest.raises(ConfigError, match="PX"):
        PowerConfig(source="PX").validate()  # type: ignore[arg-type]


def test_temperature_masks_carry_the_e5_answers() -> None:
    """DECISIONS D3/D13: absolute guard [0, 160] °C, ±10 °C around the set-point in the window."""
    extraction = default_2d_campaign().extraction
    assert extraction.temp_plausible_c == (0.0, 160.0)
    assert extraction.temp_setpoint_tolerance_c == pytest.approx(10.0)
    assert extraction.delta_t_warn_c == pytest.approx(3.0)


def test_default_box_and_target_follow_the_answers() -> None:
    """A2: EVA draws from 90 °C, safety limit 150 °C → box [90, 130] (upper confirmed, Rev. 5). E1: d* = 0.40."""
    config = default_2d_campaign()
    temp = next(v for v in config.variables if v.name == "T")
    assert (temp.lower, temp.upper) == (90.0, 130.0)
    assert config.extraction.d_star_mm == pytest.approx(0.40)
    assert config.constraint.delta_t_c == pytest.approx(1.0)


def test_objective_normalization_maps_ideal_and_nadir_to_zero_and_one() -> None:
    """§5.1: a fixed pre-campaign affine map, not one recomputed from data."""
    objective = Objective("e", "error", "mm", ref_point=0.15, ideal=0.0, nadir=0.15)
    assert objective.normalize(0.0) == pytest.approx(0.0)
    assert objective.normalize(0.15) == pytest.approx(1.0)
    assert objective.normalize(0.075) == pytest.approx(0.5)


def test_config_is_frozen() -> None:
    """Campaign edits are logged events, not in-place mutations (§7.3 item 1)."""
    config = default_2d_campaign()
    with pytest.raises(Exception):
        config.seed = 7  # type: ignore[misc]
