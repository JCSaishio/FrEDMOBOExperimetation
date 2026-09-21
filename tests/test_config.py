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
            delta_t_warn_c=3.0,
        ),
        power=PowerConfig(
            source="PX",
            columns={"heater_current": "Heater current (A)"},
            p_h_max_w=48.0,
            p_f0_w=1.5,
            spooler_calibration=[(25.0, 0.31), (50.0, 0.58)],
        ),
    )
    restored = CampaignConfig.from_json(original.to_json())
    assert restored == original
    assert restored.extraction.temp_plausible_c == (20.0, 130.0)
    assert restored.power.spooler_calibration == [(25.0, 0.31), (50.0, 0.58)]


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


def test_default_campaign_uses_mode_b_and_px() -> None:
    """§9.5: until the power PCB exists the campaign runs PX / mode B."""
    config = default_2d_campaign()
    assert config.constraint.mode == "B"
    assert config.power.source == "PX"


def test_px_power_is_flagged_incomplete_until_m3_constants_land() -> None:
    """Open items B2, B3, B4. Incomplete is the expected state, not an error."""
    assert default_2d_campaign().power.is_complete is False
    complete = PowerConfig(
        source="PX", p_h_max_w=48.0, p_f0_w=1.5, spooler_calibration=[(25.0, 0.3), (50.0, 0.6)]
    )
    assert complete.is_complete is True


def test_temperature_mask_is_off_by_default() -> None:
    """DECISIONS D3: the mask is a no-op until open item E5 supplies a range."""
    assert default_2d_campaign().extraction.temp_plausible_c is None


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
