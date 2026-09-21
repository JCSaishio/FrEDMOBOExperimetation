"""Acceptance tests for milestone M1 — space.

raw <-> unit-cube round-trip is complete. The R hand calculation and the 3D parallelogram
constraint are NOT tested here beyond asserting that they refuse to run: both are blocked on open
item A3 (effective spool diameter under load), so there is no known-good value to assert against.
See ``fred_mobo.space.draw_ratio`` and docs/PROGRESS.md.
"""

from __future__ import annotations

import pytest
import torch

from fred_mobo.config import CampaignConfig, Variable, default_2d_campaign
from fred_mobo.space import (
    DTYPE,
    bounds,
    draw_ratio,
    from_unit,
    linear_constraints,
    to_unit,
    unit_bounds,
)


@pytest.fixture
def config() -> CampaignConfig:
    return default_2d_campaign()


# ------------------------------------------------------------------ bounds


def test_bounds_shape_and_order(config: CampaignConfig) -> None:
    b = bounds(config)
    assert b.shape == (2, config.d)
    assert b.dtype is DTYPE
    torch.testing.assert_close(b[0], torch.tensor([70.0, 25.0], dtype=DTYPE))
    torch.testing.assert_close(b[1], torch.tensor([100.0, 50.0], dtype=DTYPE))


def test_bounds_columns_follow_variable_order(config: CampaignConfig) -> None:
    for j, variable in enumerate(config.variables):
        assert bounds(config)[0, j].item() == pytest.approx(variable.lower)
        assert bounds(config)[1, j].item() == pytest.approx(variable.upper)


def test_unit_bounds_is_the_unit_cube(config: CampaignConfig) -> None:
    """§8: optimize_acqf is given the unit cube."""
    u = unit_bounds(config)
    assert u.shape == (2, config.d)
    torch.testing.assert_close(u[0], torch.zeros(config.d, dtype=DTYPE))
    torch.testing.assert_close(u[1], torch.ones(config.d, dtype=DTYPE))


# ------------------------------------------------------------------ the coordinate map


def test_corners_map_to_cube_corners(config: CampaignConfig) -> None:
    raw = torch.tensor([[70.0, 25.0], [100.0, 50.0]], dtype=DTYPE)
    torch.testing.assert_close(
        to_unit(raw, config), torch.tensor([[0.0, 0.0], [1.0, 1.0]], dtype=DTYPE)
    )


def test_midpoint_maps_to_centre(config: CampaignConfig) -> None:
    raw = torch.tensor([[85.0, 37.5]], dtype=DTYPE)
    torch.testing.assert_close(to_unit(raw, config), torch.tensor([[0.5, 0.5]], dtype=DTYPE))


def test_round_trip_raw_to_unit_to_raw(config: CampaignConfig) -> None:
    raw = torch.tensor([[70.0, 25.0], [85.0, 37.5], [100.0, 50.0], [92.3, 31.7]], dtype=DTYPE)
    torch.testing.assert_close(from_unit(to_unit(raw, config), config), raw)


def test_round_trip_unit_to_raw_to_unit(config: CampaignConfig) -> None:
    generator = torch.Generator().manual_seed(0)
    unit = torch.rand(64, config.d, generator=generator, dtype=DTYPE)
    torch.testing.assert_close(to_unit(from_unit(unit, config), config), unit)


def test_map_preserves_batch_shape(config: CampaignConfig) -> None:
    """BoTorch passes ``b x q x d`` tensors; the map must not flatten them."""
    raw = torch.full((5, 3, config.d), 80.0, dtype=DTYPE)
    raw[..., 1] = 40.0
    assert to_unit(raw, config).shape == (5, 3, config.d)


def test_map_is_dimension_agnostic() -> None:
    """§7.4: 3D is a config change. The coordinate map itself needs no edit."""
    base = default_2d_campaign()
    three_d = CampaignConfig(
        variables=[*base.variables, Variable("v_f", "feed speed", "mm/min", 10.0, 30.0)],
        objectives=base.objectives,
        constraint=base.constraint,
        extraction=base.extraction,
    )
    raw = torch.tensor([[70.0, 25.0, 10.0], [100.0, 50.0, 30.0]], dtype=DTYPE)
    torch.testing.assert_close(
        to_unit(raw, three_d), torch.tensor([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=DTYPE)
    )


def test_rejects_wrong_dimension(config: CampaignConfig) -> None:
    """A silent shape mismatch here is the 'mismatched spaces' bug §8 warns about."""
    with pytest.raises(ValueError, match="trailing dimension"):
        to_unit(torch.zeros(4, 3, dtype=DTYPE), config)
    with pytest.raises(ValueError, match="trailing dimension"):
        from_unit(torch.zeros(4, 1, dtype=DTYPE), config)


def test_preserves_double_precision(config: CampaignConfig) -> None:
    """§9.2 item 1: double precision throughout."""
    assert to_unit(torch.zeros(2, config.d, dtype=DTYPE), config).dtype is DTYPE
    assert bounds(config).dtype is DTYPE


# ------------------------------------------------------------------ blocked on open item A3


def test_draw_ratio_is_blocked_not_guessed() -> None:
    """Deliberate: R is 'the leading quantity for the constraint' (§4.1).

    The core diameter (15 mm) and the diameter the observed drawdown implies (~34 mm) disagree by
    a factor of 2.3. Guessing would propagate into the constraint model, the iso-diameter
    inversion and the 3D coordinates. This test exists so the block is visible in the suite rather
    than silently absent.
    """
    with pytest.raises(NotImplementedError, match="A3"):
        draw_ratio()


def test_linear_constraints_are_blocked_transitively() -> None:
    with pytest.raises(NotImplementedError, match="A3"):
        linear_constraints()


@pytest.mark.xfail(reason="blocked on open item A3: effective spool diameter under load", strict=True)
def test_draw_ratio_against_hand_calculation() -> None:
    """The M1 acceptance test, parked until A3 lands.

    TODO(resume): with D_eff resolved, assert R against the hand calculation
    ``R = pi * D_eff * omega_s / (l_f * omega_f)`` at a set-point computed by hand, then delete
    the xfail mark and tick M1 in docs/PLAN.md.
    """
    raise NotImplementedError
